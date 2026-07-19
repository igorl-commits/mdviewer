#!/usr/bin/env python3
import sys
import os
import json
import ctypes
import webview

from debug import _DEBUG, _dlog
from assets import MARKDOWN_IT_JS, HLJS_JS, HLJS_THEMES

from config import (
    APP_VERSION,
    CONFIG_PATH,
    DEFAULTS,
    PRESETS,
    _get_version,
    _is_windows_dark_theme,
    _read_text_file,
    _update_recent_files,
    load_config,
    save_config_file,
)

def clamp_position(x, y, width: int, height: int):
    """Return (x, y) clamped to the virtual screen (all monitors combined);
    (None, None) if inputs are None. Using SM_*VIRTUALSCREEN instead of the
    primary-monitor metrics keeps windows restored on secondary monitors."""
    if x is None or y is None:
        return None, None
    try:
        user32 = ctypes.windll.user32
        vx = user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
        vy = user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
        vw = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
        vh = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
        x = max(vx, min(int(x), vx + vw - width))
        y = max(vy, min(int(y), vy + vh - height))
    except Exception:
        return 0, 0
    return x, y


class _RECT(ctypes.Structure):
    _fields_ = [('left', ctypes.c_long), ('top', ctypes.c_long),
                ('right', ctypes.c_long), ('bottom', ctypes.c_long)]


class _POINT(ctypes.Structure):
    _fields_ = [('x', ctypes.c_long), ('y', ctypes.c_long)]


def _find_hwnd(title: str):
    return ctypes.windll.user32.FindWindowW(None, title) or None


def _window_rect(hwnd):
    r = _RECT()
    if hwnd and ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r)):
        return r.left, r.top, r.right - r.left, r.bottom - r.top
    return None


def _cursor_pos():
    p = _POINT()
    if ctypes.windll.user32.GetCursorPos(ctypes.byref(p)):
        return p.x, p.y
    return None


# Win32 constants for restoring native resize on a frameless window
_GWL_STYLE = -16
_GWL_EXSTYLE = -20
_WS_THICKFRAME = 0x00040000
# SWP_NOMOVE|NOSIZE|NOZORDER|NOACTIVATE|FRAMECHANGED — force a non-client redraw
_SWP_FRAMECHANGED = 0x0001 | 0x0002 | 0x0004 | 0x0010 | 0x0020


class _MONITORINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize',   ctypes.c_uint32),
        ('rcMonitor', _RECT),
        ('rcWork',    _RECT),  # excludes taskbar
        ('dwFlags',   ctypes.c_uint32),
    ]


def _work_area_for(hwnd):
    """Work-area (excludes taskbar) of the monitor that contains the window."""
    if not hwnd:
        return None
    user32 = ctypes.windll.user32
    hmon = user32.MonitorFromWindow(hwnd, 2)  # MONITOR_DEFAULTTONEAREST
    if not hmon:
        return None
    mi = _MONITORINFO()
    mi.cbSize = ctypes.sizeof(_MONITORINFO)
    if user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
        r = mi.rcWork
        return r.left, r.top, r.right - r.left, r.bottom - r.top
    return None


def _get_required_window_size_for_client(client_w: int, client_h: int, hwnd: int):
    """Return (outer_w, outer_h) such that the window's *client* area will be
    at least (client_w, client_h) after the OS applies the current thickframe
    and other non-client borders.

    This is the key to making the "doc width" button actually deliver the
    designed prose column width instead of a "much smaller" area.
    """
    if not hwnd:
        return client_w, client_h
    try:
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, _GWL_STYLE)
        exstyle = user32.GetWindowLongW(hwnd, _GWL_EXSTYLE)
        rect = _RECT(0, 0, int(client_w), int(client_h))
        user32.AdjustWindowRectEx(ctypes.byref(rect), style, False, exstyle)
        ow = rect.right - rect.left
        oh = rect.bottom - rect.top
        return max(ow, client_w), max(oh, client_h)
    except Exception:
        return client_w, client_h


# Reading-column layout in CSS logical pixels (#page is border-box).
_PAGE_CONTENT_LOGICAL = 860
_PAGE_HPAD_LOGICAL = 48
_PAGE_MAX_LOGICAL = _PAGE_CONTENT_LOGICAL + 2 * _PAGE_HPAD_LOGICAL  # 956
_SCROLLBAR_GUTTER_LOGICAL = 24
_READING_SIDE_MARGIN_LOGICAL = 64
_TARGET_READING_CLIENT_LOGICAL = (
    _PAGE_MAX_LOGICAL + _SCROLLBAR_GUTTER_LOGICAL + 2 * _READING_SIDE_MARGIN_LOGICAL
)  # 1108


def _hwnd_dpi_scale(hwnd) -> float:
    """Physical/logical scale for hwnd (1.0 at 96 DPI)."""
    if not hwnd:
        return 1.0
    try:
        dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
        return max(dpi / 96.0, 1.0)
    except Exception:
        return 1.0


def _outer_logical_for_client_logical(client_w: int, client_h: int, hwnd: int):
    """Return outer (frame) logical size for a target client logical area."""
    scale = _hwnd_dpi_scale(hwnd)
    phys_cw = int(round(client_w * scale))
    phys_ch = int(round(client_h * scale))
    phys_ow, phys_oh = _get_required_window_size_for_client(phys_cw, phys_ch, hwnd)
    return int(round(phys_ow / scale)), int(round(phys_oh / scale))


def _geometry_from_window(api) -> tuple | None:
    """Logical-pixel window rect for config save/restore (pywebview, not GetWindowRect)."""
    w = getattr(api, '_window', None)
    if not w:
        return None
    try:
        return int(w.x), int(w.y), int(w.width), int(w.height)
    except (AttributeError, TypeError, ValueError):
        return None


def _logical_work_area_for(hwnd):
    """Work area of the monitor containing hwnd, converted to logical pixels."""
    work = _work_area_for(hwnd)
    if not work:
        return None
    scale = _hwnd_dpi_scale(hwnd)
    wx, wy, ww, wh = work
    return (int(round(wx / scale)), int(round(wy / scale)),
            int(round(ww / scale)), int(round(wh / scale)))


def _enable_native_resize(hwnd):
    """Re-add WS_THICKFRAME so the OS handles resize at window edges natively.

    pywebview's frameless mode strips this style. Without it, DefWindowProc
    ignores resize hit-tests, so the window is effectively locked in size.

    Preserves the client-area screen origin when re-applying the frame so the
    window does not jump left on the first click after focus regain.
    """
    if not hwnd:
        return
    user32 = ctypes.windll.user32
    style = user32.GetWindowLongW(hwnd, _GWL_STYLE)
    exstyle = user32.GetWindowLongW(hwnd, _GWL_EXSTYLE)
    new_style = style | _WS_THICKFRAME
    if style != new_style:
        user32.SetWindowLongW(hwnd, _GWL_STYLE, new_style)

    client_pt = _POINT()
    user32.ClientToScreen(hwnd, ctypes.byref(client_pt))
    cr = _RECT()
    user32.GetClientRect(hwnd, ctypes.byref(cr))
    client_w = cr.right - cr.left
    client_h = cr.bottom - cr.top
    rect = _RECT(0, 0, client_w, client_h)
    user32.AdjustWindowRectEx(ctypes.byref(rect), new_style, False, exstyle)
    outer_x = client_pt.x + rect.left
    outer_y = client_pt.y + rect.top
    outer_w = rect.right - rect.left
    outer_h = rect.bottom - rect.top
    # SWP_NOZORDER | NOACTIVATE | FRAMECHANGED — explicit pos/size keeps client fixed
    user32.SetWindowPos(hwnd, 0, outer_x, outer_y, outer_w, outer_h, 0x0004 | 0x0010 | 0x0020)
    _dlog('_enable_native_resize: WS_THICKFRAME applied hwnd=%s client=%sx%s outer=%sx%s',
          hwnd, client_w, client_h, outer_w, outer_h)


class Api:
    def __init__(self, md_path: str, title: str):
        self._md_path = md_path
        self._title = title
        self._window = None  # set after webview.create_window
        self._hwnd = None
        # Last known non-fullscreen rect in pywebview logical pixels (x, y, w, h).
        self._pre_fullscreen_rect = None
        self._geom_save_timer = None

    def _ensure_hwnd(self):
        if not self._hwnd:
            self._hwnd = _find_hwnd(self._title)
            _dlog('Api._ensure_hwnd resolved hwnd=%s', self._hwnd)
        return self._hwnd

    def get_file(self) -> str:
        _dlog('Api.get_file path=%s', self._md_path)
        if not self._md_path:
            return ''
        data = _read_text_file(self._md_path)
        _dlog('Api.get_file returned %d bytes', len(data))
        return data

    def save_config(self, data: dict) -> None:
        _dlog('Api.save_config partial=%s', data)
        current = load_config()
        for k in ('theme', 'preset'):
            if k in data:
                current[k] = data[k]
        rect = _geometry_from_window(self)
        if rect:
            x, y, w, h = rect
            current['window'] = {'width': w, 'height': h, 'x': x, 'y': y}
        save_config_file(current)

    def _schedule_save_geometry(self) -> None:
        """Debounced geometry save for moved/resized events."""
        import threading
        if self._geom_save_timer is not None:
            try:
                self._geom_save_timer.cancel()
            except Exception:
                pass

        def _fire():
            self._geom_save_timer = None
            self._save_geometry()

        self._geom_save_timer = threading.Timer(0.35, _fire)
        self._geom_save_timer.daemon = True
        self._geom_save_timer.start()

    def _save_geometry(self) -> None:
        """Persist the current (or pre-fullscreen) window position and size.

        If the window is currently in fullscreen mode, we save the last known
        non-fullscreen rect instead, so the user doesn't get a giant/maximized
        window on the next launch.
        """
        try:
            is_fullscreen = False
            if self._window is not None:
                is_fullscreen = bool(getattr(self._window, 'fullscreen', False))

            if is_fullscreen and self._pre_fullscreen_rect:
                rect = self._pre_fullscreen_rect
            else:
                rect = _geometry_from_window(self)
                if rect and not is_fullscreen:
                    self._pre_fullscreen_rect = rect

            if rect:
                current = load_config()
                current['window'] = {'width': rect[2], 'height': rect[3],
                                     'x': rect[0], 'y': rect[1]}
                save_config_file(current)
                _dlog('_save_geometry: saved %s (was_fullscreen=%s)', current['window'], is_fullscreen)
        except Exception as e:
            _dlog('_save_geometry FAILED: %s', e)

    def refresh_resize_handles(self) -> None:
        """Re-apply WS_THICKFRAME if it was lost.
        Called from JS on 'focus' event (after Alt-Tab, task switch, etc.)
        so the first click on the custom titlebar buttons works reliably
        instead of being eaten by activation.
        Must be public: pywebview never exposes underscore-prefixed methods to JS.
        """
        _enable_native_resize(self._ensure_hwnd())

    def force_activate(self) -> None:
        """Explicitly activate the window. Helps deliver the first mouse click
        after the window regains focus via Alt-Tab or similar.
        Must be public: pywebview never exposes underscore-prefixed methods to JS.
        """
        hwnd = self._ensure_hwnd()
        if hwnd:
            user32 = ctypes.windll.user32
            user32.SetForegroundWindow(hwnd)
            user32.SetActiveWindow(hwnd)

    def close_window(self) -> None:
        _dlog('Api.close_window')
        self._save_geometry()
        if self._window:
            self._window.destroy()

    def toggle_fullscreen(self) -> None:
        _dlog('Api.toggle_fullscreen')
        if self._window:
            # Capture current size/position *before* we enter fullscreen
            currently_full = bool(getattr(self._window, 'fullscreen', False))
            if not currently_full:
                rect = _geometry_from_window(self)
                if rect:
                    self._pre_fullscreen_rect = rect
                    _dlog('toggle_fullscreen: captured pre-fullscreen rect %s', rect)

            self._window.toggle_fullscreen()
            # pywebview resets FormBorderStyle on toggle, stripping WS_THICKFRAME.
            # Re-apply so resize keeps working after returning from fullscreen.
            _enable_native_resize(self._ensure_hwnd())

    def snap(self, mode: str) -> None:
        """Snap window to a layout on the current monitor.

        mode in {'left', 'right', 'reading'}
          left/right : half of the work area
          reading    : "doc width" — the prose column exactly as designed (using
                       AdjustWindowRectEx so thickframe does not eat the client area),
                       centered on the monitor, with maximum (workarea) height.
        """
        _dlog('Api.snap mode=%s', mode)

        # Always prefer a *fresh* FindWindowW by title for geometry operations.
        # The old forever-cached hwnd (from _ensure_hwnd) became stale after
        # previous snaps, fullscreen toggles, or style changes → first click
        # used wrong monitor/workarea (window "shifted left"), second click worked.
        hwnd = _find_hwnd(self._title)
        if not hwnd:
            hwnd = self._ensure_hwnd()
        work = _work_area_for(hwnd)
        if not hwnd or not work:
            return
        wx, wy, ww, wh = work

        if mode == 'left':
            x, y, w, h = wx, wy, ww // 2, wh
        elif mode == 'right':
            x, y, w, h = wx + ww - ww // 2, wy, ww // 2, wh
        elif mode == 'reading':
            # DPI-aware doc-width snap via pywebview logical pixels.
            work_log = _logical_work_area_for(hwnd)
            if not work_log or not self._window:
                return
            lwx, lwy, lww, lwh = work_log
            cw = _TARGET_READING_CLIENT_LOGICAL
            ow, oh = _outer_logical_for_client_logical(cw, lwh, hwnd)
            ow = min(ow, lww)
            x = lwx + (lww - ow) // 2
            y = lwy
            self._window.move(x, y)
            self._window.resize(ow, oh)
            try:
                ctypes.windll.user32.UpdateWindow(hwnd)
            except Exception:
                pass
            self._save_geometry()
            return
        else:
            return

        # SWP_NOZORDER | SWP_NOACTIVATE
        ctypes.windll.user32.SetWindowPos(hwnd, 0, int(x), int(y), int(w), int(h), 0x0014)

        # Help the window settle so a rapid next button click immediately sees
        # the new position + correct monitor/workarea (fixes the "click twice" symptom).
        try:
            ctypes.windll.user32.UpdateWindow(hwnd)
        except Exception:
            pass

        self._save_geometry()   # remember the new snapped layout for next launch

    def js_log(self, msg: str) -> None:
        """JS calls this to forward console messages into the Python debug log."""
        _dlog('JS: %s', msg)

    def load_dropped_file(self, filename: str, content: str) -> None:
        """Replace the current view with the content of a dropped .md file.
        Keeps the app lightweight (no new window, no temp files).
        """
        _dlog('Api.load_dropped_file: %s (%d bytes)', filename, len(content))
        # Dropped content has no filesystem path — stop the live-reload watcher
        # from re-rendering the previous file over it.
        self._md_path = None
        self._title = filename  # keep title-based hwnd lookup (snap) working
        try:
            if self._window:
                self._window.set_title(filename)
                self._window.evaluate_js(f'''
                    (function() {{
                        const contentEl = document.getElementById('content');
                        if (!contentEl) return;
                        const raw = {json.dumps(content)};
                        const rendered = md.render(raw);
                        const frag = document.createRange().createContextualFragment(rendered);
                        contentEl.replaceChildren(frag);
                    }})();
                ''')
        except Exception as e:
            _dlog('load_dropped_file render failed: %s', e)

    def get_recent_files(self) -> list:
        """Return the list of recently opened files (for the gear menu)."""
        try:
            cfg = load_config()
            return cfg.get('recent', [])[:8]
        except Exception:
            return []

    def open_recent(self, path: str) -> None:
        """Open a file from the recent list (re-renders in place, lightweight)."""
        _dlog('Api.open_recent: %s', path)
        if not os.path.isfile(path):
            return
        try:
            _update_recent_files(path)
            self._md_path = path
            self._title = os.path.basename(path)
            if self._window:
                self._window.set_title(self._title)
                self._window.evaluate_js('reloadFromDisk();')
        except Exception as e:
            _dlog('open_recent failed: %s', e)

def build_html(config: dict) -> str:
    presets_json      = json.dumps(HLJS_THEMES)
    presets_list_json = json.dumps(PRESETS)
    stored_theme      = config.get('theme', 'dark')
    init_theme        = stored_theme if stored_theme != 'system' else ('dark' if _is_windows_dark_theme() else 'light')
    init_preset       = config['preset']
    version           = APP_VERSION

    return (
        """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style id="hljs-theme"></style>
<style>
:root {
  --bg:#1e1e2e;--fg:#cdd6f4;--heading:#cba6f7;--link:#89b4fa;
  --code-bg:#313244;--border:#45475a;--muted:#6c7086;
  --menu-bg:#2a2a3e;--menu-border:#45475a;--menu-hover:#313244;--menu-fg:#cdd6f4;
}
[data-theme="light"] {
  --bg:#ffffff;--fg:#24292f;--heading:#6639ba;--link:#0969da;
  --code-bg:#f6f8fa;--border:#d0d7de;--muted:#57606a;
  --menu-bg:#ffffff;--menu-border:#d0d7de;--menu-hover:#f6f8fa;--menu-fg:#24292f;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{
  background:var(--bg);color:var(--fg);
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  font-size:15px;line-height:1.7;
  -webkit-app-region:drag;user-select:none;
}
#page{max-width:956px;margin:0 auto;padding:36px 48px 64px;-webkit-app-region:drag}
#page a,#page code,#page pre,#page table,#page input,#page img{
  -webkit-app-region:no-drag;user-select:text;
}
#controls{
  position:fixed;top:8px;right:10px;display:flex;gap:4px;
  opacity:0;transition:opacity .2s;z-index:200;-webkit-app-region:no-drag;
}
body:hover #controls{opacity:1}

#version{
  position:fixed;bottom:6px;left:10px;font-size:10px;color:var(--muted);
  opacity:0;transition:opacity .2s;z-index:150;-webkit-app-region:no-drag;
  pointer-events:none;
}
body:hover #version{opacity:0.6}

/* Lightweight image lightbox */
#img-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.85);
  display: none; align-items: center; justify-content: center; z-index: 9999;
  cursor: zoom-out;
}
#img-overlay img {
  max-width: 95vw; max-height: 95vh; object-fit: contain;
  box-shadow: 0 10px 40px rgba(0,0,0,0.6);
}

/* Search highlight */
mark.search-hit {
  background: #f9d71c;
  color: #222;
  border-radius: 2px;
  padding: 0 1px;
}
mark.search-current {
  background: #f77d05;
  color: white;
}

.ctrl-btn{
  background:rgba(128,128,128,.15);border:none;border-radius:5px;
  color:var(--fg);cursor:pointer;font-size:14px;line-height:1;
  padding:5px 9px;-webkit-app-region:no-drag;transition:background .15s;
}
.ctrl-btn:hover{background:rgba(128,128,128,.35)}
#ctx-menu{
  position:fixed;background:var(--menu-bg);border:1px solid var(--menu-border);
  border-radius:8px;box-shadow:0 8px 28px rgba(0,0,0,.35);
  padding:5px 0;min-width:190px;z-index:1000;-webkit-app-region:no-drag;
}
.ctx-item{cursor:pointer;font-size:13px;padding:6px 14px;color:var(--menu-fg);white-space:nowrap}
.ctx-item:hover{background:var(--menu-hover)}
.ctx-item.active{font-weight:600}
.ctx-divider{border-top:1px solid var(--menu-border);margin:4px 0}
.ctx-label{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);padding:4px 14px 2px}
h1,h2,h3,h4,h5,h6{color:var(--heading);margin:1.4em 0 .5em;font-weight:600}
h1{font-size:2em;margin-top:.6em}
h2{font-size:1.5em;border-bottom:1px solid var(--border);padding-bottom:.3em}
h3{font-size:1.25em}
p{margin:.8em 0}
a{color:var(--link);text-decoration:none}
a:hover{text-decoration:underline}
ul,ol{margin:.6em 0 .6em 1.6em}
li{margin:.2em 0}
blockquote{border-left:3px solid var(--border);color:var(--muted);margin:1em 0;padding:.3em 1em}
code{
  background:var(--code-bg);border-radius:4px;
  font-family:'Cascadia Code','Fira Code','Consolas',monospace;
  font-size:.88em;padding:.15em .4em;
  -webkit-app-region:no-drag;user-select:text;
}
pre{
  background:var(--code-bg);border-radius:8px;margin:1em 0;
  overflow-x:auto;padding:1em 1.2em;
  -webkit-app-region:no-drag;user-select:text;
}
pre code{background:none;font-size:.9em;padding:0}
table{border-collapse:collapse;margin:1em 0;width:100%}
th,td{border:1px solid var(--border);padding:.5em .9em;text-align:left}
th{background:var(--code-bg);font-weight:600}
tr:nth-child(even) td{background:rgba(128,128,128,.05)}
img{max-width:100%;border-radius:4px}
hr{border:none;border-top:1px solid var(--border);margin:1.5em 0}
input[type="checkbox"]{margin-right:.4em;-webkit-app-region:no-drag}
/* Floating auto-hiding scrollbar — overlay only, no track, fades in on use */
::-webkit-scrollbar{width:8px;height:8px;background:transparent}
::-webkit-scrollbar-track{background:transparent;border:none}
::-webkit-scrollbar-thumb{
  background:transparent;
  border-radius:8px;
  border:none;
  transition:background .25s ease;
}
::-webkit-scrollbar-corner{background:transparent}
/* Reveal thumb while actively scrolling OR pointer is over content */
html.scrolling ::-webkit-scrollbar-thumb,
body:hover ::-webkit-scrollbar-thumb{background:rgba(128,128,128,.3)}
html.scrolling ::-webkit-scrollbar-thumb:hover,
body:hover ::-webkit-scrollbar-thumb:hover{background:rgba(128,128,128,.55)}
html{scrollbar-width:thin;scrollbar-color:transparent transparent;transition:scrollbar-color .25s}
html.scrolling,html:hover{scrollbar-color:rgba(128,128,128,.3) transparent}
</style>
</head>
<body data-theme="__THEME__">
<div id="controls">
  <button class="ctrl-btn" id="btn-tall"  title="Doc width, full height">&#9647;</button>
  <button class="ctrl-btn" id="btn-left"  title="Snap left half">&#9703;</button>
  <button class="ctrl-btn" id="btn-right" title="Snap right half">&#9704;</button>
  <button class="ctrl-btn" id="btn-full"  title="Fullscreen (F11)">&#9974;</button>
  <button class="ctrl-btn" id="btn-gear"  title="Settings">&#9881;</button>
  <button class="ctrl-btn" id="btn-close" title="Close">&#10005;</button>
</div>
<div id="page"><div id="content"></div></div>
<div id="ctx-menu" hidden></div>
<div id="version">v__VERSION__</div>
<div id="img-overlay"><img alt=""></div>

<!-- Lightweight in-document search -->
<div id="search-bar" style="display:none;position:fixed;top:8px;left:50%;transform:translateX(-50%);z-index:1000;background:var(--menu-bg);border:1px solid var(--menu-border);border-radius:6px;padding:4px 8px;box-shadow:0 4px 12px rgba(0,0,0,0.3);font-size:13px;">
  <input id="search-input" placeholder="Search..." style="background:transparent;border:none;outline:none;color:var(--menu-fg);width:220px;">
  <span id="search-count" style="margin:0 6px;color:var(--muted);font-size:11px;"></span>
  <button id="search-prev" style="background:none;border:none;color:var(--menu-fg);cursor:pointer;">↑</button>
  <button id="search-next" style="background:none;border:none;color:var(--menu-fg);cursor:pointer;">↓</button>
  <button id="search-close" style="background:none;border:none;color:var(--muted);cursor:pointer;margin-left:4px;">✕</button>
</div>
<script>__MARKDOWN_IT_JS__</script>
<script>__HLJS_JS__</script>
<script>
const THEMES = __PRESETS_JSON__;
const PRESETS = __PRESETS_LIST_JSON__;

let currentTheme  = '__STORED_THEME__';   // can be 'dark', 'light', or 'system'
let currentPreset = '__PRESET__';

const hljsStyle = document.getElementById('hljs-theme');
const ctxMenu   = document.getElementById('ctx-menu');

// THEME-CYCLE-LOGIC-START
function effectiveTheme(t) {
  if (t !== 'system') return t;
  const isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  return isDark ? 'dark' : 'light';
}

// Cycle dark -> light -> system -> dark, skipping any state that would look
// identical to the current appearance — every click must visibly change the page.
function nextTheme() {
  const order = {dark: ['light', 'system'], light: ['system', 'dark'], system: ['dark', 'light']};
  const cur = effectiveTheme(currentTheme);
  for (const cand of (order[currentTheme] || ['dark', 'light'])) {
    if (effectiveTheme(cand) !== cur) return cand;
  }
  return cur === 'dark' ? 'light' : 'dark';
}
// THEME-CYCLE-LOGIC-END

function setTheme(t) {
  currentTheme = t;
  document.body.dataset.theme = effectiveTheme(t);
  persistSettings();
}

function setPreset(key) {
  currentPreset = key;
  hljsStyle.textContent = THEMES[key] || '';
  ctxMenu.querySelectorAll('.preset-item').forEach(el => {
    el.textContent = (el.dataset.key === key ? '\\u2713  ' : '    ') + el.dataset.label;
    el.classList.toggle('active', el.dataset.key === key);
  });
  persistSettings();
}

function persistSettings() {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.save_config) {
    pywebview.api.save_config({theme: currentTheme, preset: currentPreset});
  }
}

if (window.matchMedia) {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (currentTheme === 'system') {
      document.body.dataset.theme = effectiveTheme('system');
    }
  });
}

async function buildMenu(x, y) {
  ctxMenu.replaceChildren();

  // Theme row
  // Label names the *next* state from nextTheme(), which skips visual no-ops.
  const themeItem = document.createElement('div');
  themeItem.className = 'ctx-item';
  const nextT = nextTheme();
  if (nextT === 'light') {
    themeItem.textContent = '\\u2600  Switch to Light';
  } else if (nextT === 'system') {
    themeItem.textContent = '\\u2699\\uFE0F  Follow System';
  } else {
    themeItem.textContent = '\\uD83C\\uDF19  Switch to Dark';
  }
  themeItem.onclick = () => {
    setTheme(nextT);
    closeMenu();
  };
  ctxMenu.appendChild(themeItem);

  ctxMenu.appendChild(Object.assign(document.createElement('div'), {className: 'ctx-divider'}));

  // Recent files (lightweight). pywebview API calls return Promises — must await.
  const recent = (window.pywebview && window.pywebview.api && window.pywebview.api.get_recent_files)
    ? await window.pywebview.api.get_recent_files() : [];
  if (recent.length > 0) {
    const recentLbl = document.createElement('div');
    recentLbl.className = 'ctx-label';
    recentLbl.textContent = 'Recent';
    ctxMenu.appendChild(recentLbl);

    recent.forEach(p => {
      const item = document.createElement('div');
      item.className = 'ctx-item';
      const name = p.split(/[\\/]/).pop();
      item.textContent = '  ' + name;
      item.title = p;
      item.onclick = () => {
        closeMenu();
        if (window.pywebview && window.pywebview.api && window.pywebview.api.open_recent) {
          pywebview.api.open_recent(p);
        }
      };
      ctxMenu.appendChild(item);
    });

    ctxMenu.appendChild(Object.assign(document.createElement('div'), {className: 'ctx-divider'}));
  }

  const lbl = document.createElement('div');
  lbl.className = 'ctx-label';
  lbl.textContent = 'Syntax Theme';
  ctxMenu.appendChild(lbl);

  PRESETS.forEach(([key, label]) => {
    const item = document.createElement('div');
    item.className = 'ctx-item preset-item';
    item.dataset.key   = key;
    item.dataset.label = label;
    item.textContent   = (key === currentPreset ? '\\u2713  ' : '    ') + label;
    if (key === currentPreset) item.classList.add('active');
    item.onclick = () => { setPreset(key); closeMenu(); };
    ctxMenu.appendChild(item);
  });

  ctxMenu.hidden = false;
  const mw = ctxMenu.offsetWidth, mh = ctxMenu.offsetHeight;
  ctxMenu.style.left = Math.min(x, window.innerWidth  - mw - 8) + 'px';
  ctxMenu.style.top  = Math.min(y, window.innerHeight - mh - 8) + 'px';
}

function closeMenu() { ctxMenu.hidden = true; }

document.addEventListener('contextmenu', e => { e.preventDefault(); buildMenu(e.clientX, e.clientY); });
document.addEventListener('click', e => { if (!ctxMenu.contains(e.target)) closeMenu(); });
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeMenu();
  if (e.key === 'F11') { e.preventDefault(); pywebview.api.toggle_fullscreen(); }
});

// Lightweight drag & drop support for .md files
document.addEventListener('dragover', e => {
  e.preventDefault();
  e.dataTransfer.dropEffect = 'copy';
});
document.addEventListener('drop', e => {
  e.preventDefault();
  const file = e.dataTransfer.files[0];
  if (!file) return;
  if (!file.name.toLowerCase().endsWith('.md') && !file.name.toLowerCase().endsWith('.markdown')) {
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.load_dropped_file) {
      pywebview.api.load_dropped_file(file.name, reader.result);
    }
  };
  reader.readAsText(file);
});

// === Lightweight in-document search (Ctrl+F) ===
(function() {
  const bar = document.getElementById('search-bar');
  const input = document.getElementById('search-input');
  const countEl = document.getElementById('search-count');
  const btnPrev = document.getElementById('search-prev');
  const btnNext = document.getElementById('search-next');
  const btnClose = document.getElementById('search-close');

  if (!bar || !input) return;

  let matches = [];
  let currentIndex = -1;

  function clearHighlights() {
    document.querySelectorAll('mark.search-hit, mark.search-current').forEach(m => {
      const parent = m.parentNode;
      parent.replaceChild(document.createTextNode(m.textContent), m);
      parent.normalize();
    });
    matches = [];
    currentIndex = -1;
    if (countEl) countEl.textContent = '';
  }

  function doSearch() {
    clearHighlights();
    const term = input.value.trim();
    if (!term) return;

    const walker = document.createTreeWalker(
      document.getElementById('content'),
      NodeFilter.SHOW_TEXT,
      null
    );

    const found = [];
    let node;
    while ((node = walker.nextNode())) {
      const text = node.nodeValue;
      const lower = text.toLowerCase();
      let pos = 0;
      while ((pos = lower.indexOf(term.toLowerCase(), pos)) !== -1) {
        found.push({ node, start: pos, length: term.length });
        pos += term.length;
      }
    }

    // Wrap matches
    found.reverse().forEach(hit => {
      const { node, start, length } = hit;
      const before = node.nodeValue.slice(0, start);
      const match = node.nodeValue.slice(start, start + length);
      const after = node.nodeValue.slice(start + length);

      const mark = document.createElement('mark');
      mark.className = 'search-hit';
      mark.textContent = match;

      const frag = document.createDocumentFragment();
      if (before) frag.appendChild(document.createTextNode(before));
      frag.appendChild(mark);
      if (after) frag.appendChild(document.createTextNode(after));

      node.parentNode.replaceChild(frag, node);
    });

    matches = Array.from(document.querySelectorAll('mark.search-hit'));
    currentIndex = matches.length ? 0 : -1;
    updateCurrent();
  }

  function updateCurrent() {
    matches.forEach((m, i) => m.classList.toggle('search-current', i === currentIndex));
    if (countEl) {
      countEl.textContent = matches.length ? `${currentIndex + 1}/${matches.length}` : '';
    }
    if (currentIndex >= 0) {
      matches[currentIndex].scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
  }

  function next() {
    if (!matches.length) return;
    currentIndex = (currentIndex + 1) % matches.length;
    updateCurrent();
  }
  function prev() {
    if (!matches.length) return;
    currentIndex = (currentIndex - 1 + matches.length) % matches.length;
    updateCurrent();
  }

  function closeSearch() {
    bar.style.display = 'none';
    clearHighlights();
    input.value = '';
  }

  // Keyboard trigger
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'f') {
      e.preventDefault();
      bar.style.display = 'block';
      input.focus();
      input.select();
    }
    if (e.key === 'Escape' && bar.style.display !== 'none') {
      closeSearch();
    }
    if (e.key === 'Enter' && document.activeElement === input) {
      e.preventDefault();
      if (matches.length === 0) doSearch();
      else next();
    }
  });

  let _searchDebounce = null;
  input.addEventListener('input', () => {
    clearTimeout(_searchDebounce);
    _searchDebounce = setTimeout(() => {
      if (input.value.trim().length >= 2) {
        doSearch();
      } else {
        clearHighlights();
      }
    }, 150);
  });

  btnNext && btnNext.addEventListener('click', next);
  btnPrev && btnPrev.addEventListener('click', prev);
  btnClose && btnClose.addEventListener('click', closeSearch);
})();

// Simple image lightbox (click any rendered image to enlarge)
const imgOverlay = document.getElementById('img-overlay');
const overlayImg = imgOverlay ? imgOverlay.querySelector('img') : null;

document.addEventListener('click', e => {
  if (e.target.tagName === 'IMG' && e.target.closest('#content') && overlayImg) {
    overlayImg.src = e.target.src;
    imgOverlay.style.display = 'flex';
  }
});
if (imgOverlay) {
  imgOverlay.addEventListener('click', () => { imgOverlay.style.display = 'none'; });
}
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && imgOverlay && imgOverlay.style.display === 'flex') {
    imgOverlay.style.display = 'none';
  }
});

document.getElementById('btn-gear').addEventListener('click', e => {
  e.stopPropagation();
  const r = e.currentTarget.getBoundingClientRect();
  buildMenu(r.left, r.bottom + 4);
});

document.getElementById('btn-close').addEventListener('mousedown', (e) => {
  e.stopPropagation();
});
document.getElementById('btn-close').addEventListener('click', () => {
  pywebview.api.close_window();
});

document.getElementById('btn-tall').addEventListener('click', () => {
  pywebview.api.snap('reading');
});

document.getElementById('btn-left').addEventListener('click',  () => pywebview.api.snap('left'));
document.getElementById('btn-right').addEventListener('click', () => pywebview.api.snap('right'));
document.getElementById('btn-full').addEventListener('click',  () => pywebview.api.toggle_fullscreen());
// Window movement: pywebview easy_drag handles drag via -webkit-app-region: drag.
// Window resize: native Win32 (WS_THICKFRAME added on load, OS handles edges).

const md = markdownit({
  html: false,
  linkify: true,
  typographer: true,
  highlight: (str, lang) => {
    let body;
    if (lang && hljs.getLanguage(lang)) {
      try { body = hljs.highlight(str, {language: lang, ignoreIllegals: true}).value; } catch (_) {}
    }
    if (!body) body = hljs.highlightAuto(str).value;
    return '<pre class="hljs"><code>' + body + '</code></pre>';
  }
});

function jslog(msg) {
  try { if (window.pywebview && window.pywebview.api && window.pywebview.api.js_log) pywebview.api.js_log(String(msg)); } catch(_) {}
  console.log(msg);
}

async function reloadFromDisk() {
  const contentEl = document.getElementById('content');
  if (!contentEl) return;
  try {
    const raw = await pywebview.api.get_file();
    const rendered = md.render(raw);
    const frag = document.createRange().createContextualFragment(rendered);
    contentEl.replaceChildren(frag);
  } catch (e) {
    jslog('reloadFromDisk failed: ' + e);
  }
}

async function init() {
  jslog('init() entered');
  const contentEl = document.getElementById('content');
  try {
    jslog('init: calling get_file');
    const raw = await pywebview.api.get_file();
    jslog('init: got ' + raw.length + ' bytes');
    const rendered = md.render(raw);
    jslog('init: rendered ' + rendered.length + ' chars of HTML');
    const frag = document.createRange().createContextualFragment(rendered);
    contentEl.replaceChildren(frag);
    setPreset(currentPreset);
    setTheme(currentTheme);
    jslog('init: done');
  } catch (e) {
    jslog('init FAILED: ' + e);
    const errEl = Object.assign(document.createElement('p'), {
      textContent: 'Failed to load file: ' + e,
    });
    errEl.style.cssText = 'color:var(--muted);padding:2em';
    contentEl.replaceChildren(errEl);
  }
}

// Robust init triggering: event listener + polling + failsafe.
// pywebviewready may have already fired before this script ran, so we poll too.
let _inited = false;
function tryInit() {
  if (_inited) return;
  if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_file === 'function') {
    _inited = true;
    init();
  }
}
// Auto-hide scrollbar: add `scrolling` class while wheel/scroll happens, clear after pause
let _scrollHideTimer = null;
function markScrolling() {
  document.documentElement.classList.add('scrolling');
  clearTimeout(_scrollHideTimer);
  _scrollHideTimer = setTimeout(() => {
    document.documentElement.classList.remove('scrolling');
  }, 900);
}
window.addEventListener('scroll', markScrolling, {passive: true});
window.addEventListener('wheel',  markScrolling, {passive: true});

window.addEventListener('pywebviewready', tryInit);
let _polls = 0;
const _pollId = setInterval(() => {
  _polls++;
  tryInit();
  if (_inited || _polls > 200) clearInterval(_pollId);
}, 50);

// Re-apply thickframe on focus regain (debounced — avoids fighting the first click).
let _focusRefreshTimer = null;
window.addEventListener('focus', () => {
  clearTimeout(_focusRefreshTimer);
  _focusRefreshTimer = setTimeout(() => {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.refresh_resize_handles) {
      pywebview.api.refresh_resize_handles();
    }
  }, 50);
});

// On mousedown in the button area (except close), explicitly activate the window.
const controls = document.getElementById('controls');
if (controls) {
  controls.addEventListener('mousedown', (e) => {
    if (e.target.closest('#btn-close')) return;
    if (window.pywebview && window.pywebview.api && window.pywebview.api.force_activate) {
      pywebview.api.force_activate();
    }
  }, { capture: true });
}

setTimeout(() => {
  if (!_inited) {
    document.getElementById('content').textContent =
      'pywebview API never became available after 10s. Check pywebview installation.';
  }
}, 10000);
</script>
</body>
</html>"""
        .replace('__MARKDOWN_IT_JS__', MARKDOWN_IT_JS)
        .replace('__HLJS_JS__',        HLJS_JS)
        .replace('__PRESETS_JSON__',      presets_json)
        .replace('__PRESETS_LIST_JSON__', presets_list_json)
        .replace('__THEME__',        init_theme)
        .replace('__STORED_THEME__', stored_theme)
        .replace('__PRESET__',       init_preset)
        .replace('__VERSION__',      version)
    )


def main() -> None:
    if len(sys.argv) < 2:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            title='Open Markdown file',
            filetypes=[('Markdown', '*.md *.markdown'), ('All files', '*.*')],
        )
        root.destroy()
        if not path:
            return
    else:
        path = sys.argv[1]

    if not os.path.isfile(path):
        import tkinter as tk
        import tkinter.messagebox as mb
        root = tk.Tk()
        root.withdraw()
        mb.showerror('MD Viewer', f'File not found:\n{path}')
        root.destroy()
        return

    config = load_config()
    win    = config['window']
    x, y  = clamp_position(win.get('x'), win.get('y'), win['width'], win['height'])

    _update_recent_files(path)   # lightweight recent files tracking

    title = os.path.basename(path)
    _dlog('main: opening file=%s title=%s window=%s', path, title, win)
    api   = Api(path, title)
    window = webview.create_window(
        title=title,
        html=build_html(config),
        js_api=api,
        frameless=True,
        easy_drag=True,  # pywebview JS-side drag via -webkit-app-region:drag
        width=win['width'],
        height=win['height'],
        x=x,
        y=y,
        min_size=(400, 300),
    )
    api._window = window

    # Lightweight live reload using stdlib polling (no extra deps).
    # Follows api._md_path so it tracks the file currently displayed —
    # open_recent retargets it, drag & drop (path=None) suspends it.
    def _start_file_watcher(api_instance, interval=1.2):
        import threading, time, os
        watched = {'path': api_instance._md_path, 'mtime': None}
        try:
            watched['mtime'] = os.path.getmtime(watched['path'])
        except OSError:
            pass

        def watcher():
            while True:
                time.sleep(interval)
                file_path = api_instance._md_path
                if not file_path:
                    watched['path'] = None
                    continue
                try:
                    if file_path != watched['path']:
                        # Displayed file changed (open_recent) — rebase, don't reload.
                        watched['path'] = file_path
                        watched['mtime'] = os.path.getmtime(file_path)
                        continue
                    mtime = os.path.getmtime(file_path)
                    if mtime != watched['mtime']:
                        watched['mtime'] = mtime
                        if api_instance._window:
                            api_instance._window.evaluate_js('reloadFromDisk();')
                        _dlog('File watcher: reloaded %s', file_path)
                except Exception as e:
                    _dlog('File watcher error: %s', e)

        t = threading.Thread(target=watcher, daemon=True)
        t.start()

    _start_file_watcher(api)

    def on_loaded():
        # Restore WS_THICKFRAME so the OS handles resize at window edges.
        # pywebview's frameless mode strips it; without it, the window is fixed-size.
        _enable_native_resize(api._ensure_hwnd())

    window.events.loaded += on_loaded
    window.events.resized += lambda e: api._schedule_save_geometry()
    window.events.moved += lambda e: api._schedule_save_geometry()

    def on_closing():
        if api._geom_save_timer is not None:
            try:
                api._geom_save_timer.cancel()
            except Exception:
                pass
            api._geom_save_timer = None
        api._save_geometry()

    window.events.closing += on_closing
    _dlog('main: calling webview.start(debug=%s)', _DEBUG)
    webview.start(debug=_DEBUG)


if __name__ == '__main__':
    main()
