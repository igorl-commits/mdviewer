"""pywebview JS bridge (Api). Non-callable attrs must be _-prefixed."""
import base64
import ctypes
import json
import mimetypes
import os
import threading
import time

from config import (
    _read_text_file,
    _update_recent_files,
    load_config,
    save_config_file,
)
from debug import _diag, _dlog
from geometry import (
    _TARGET_READING_CLIENT_LOGICAL,
    _enable_native_resize,
    _find_hwnd,
    _geometry_from_window,
    _logical_work_area_for,
    _outer_logical_for_client_logical,
    _work_area_for,
)


def resolve_media_ref(ref: str, base_dir: str | None) -> str:
    """Resolve a markdown image/src ref for the embedded HTML page.

    Relative paths are joined to *base_dir* (directory of the open .md file) and
    embedded as data URIs. Remote/data URLs are returned unchanged. Missing
    files return *ref* unchanged so the broken-image UI stays honest.
    """
    if not ref:
        return ref
    s = ref.strip()
    lower = s.lower()
    if lower.startswith(('http://', 'https://', 'data:', 'blob:')):
        return s
    if lower.startswith('file:'):
        return s

    path_part = s.split('?', 1)[0].split('#', 1)[0]
    if os.path.isabs(path_part):
        full = path_part
    else:
        if not base_dir:
            return s
        full = os.path.normpath(os.path.join(base_dir, path_part))

    if not os.path.isfile(full):
        return s
    try:
        with open(full, 'rb') as f:
            data = f.read()
    except OSError:
        return s
    mime = mimetypes.guess_type(full)[0] or 'application/octet-stream'
    b64 = base64.b64encode(data).decode('ascii')
    return f'data:{mime};base64,{b64}'


class Api:
    def __init__(self, md_path: str, title: str):
        self._md_path = md_path
        self._title = title
        self._window = None  # set after webview.create_window
        self._hwnd = None
        # Last known non-fullscreen rect in pywebview logical pixels (x, y, w, h).
        self._pre_fullscreen_rect = None
        self._geom_save_timer = None
        self._custom_drag_stop = None
        self._custom_drag_active = False

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

    def resolve_media(self, ref: str) -> str:
        """JS calls this after render to turn relative img src into data URIs."""
        base = os.path.dirname(self._md_path) if self._md_path else None
        out = resolve_media_ref(ref, base)
        if out != ref:
            _dlog('Api.resolve_media embedded %s (%d chars)', ref, len(out))
        return out

    def save_config(self, data: dict) -> None:
        _dlog('Api.save_config partial=%s', data)
        current = load_config()
        if 'theme' in data:
            current['theme'] = data['theme']
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

    def native_drag(self) -> None:
        """Start a native Win32 window move from a draggable page area.

        pywebview's easy_drag path computes a new absolute position in JS from
        screenX/clientX. On scaled WebView2 displays that can produce a bogus x
        coordinate, so a tiny post-click mousemove may make the window jump left.
        Let Windows run the caption-drag loop instead.
        Must be public: JS calls it through pywebview.api.native_drag().
        """
        _diag('native_drag entered title=%s', self._title)
        hwnd = _find_hwnd(self._title) or self._ensure_hwnd()
        _diag('native_drag hwnd=%s', hwnd)
        if not hwnd:
            _diag('native_drag NO HWND, aborting')
            return
        try:
            user32 = ctypes.windll.user32
            fg = user32.SetForegroundWindow(hwnd)
            rel = user32.ReleaseCapture()
            rect = ctypes.wintypes.RECT()
            got = user32.GetWindowRect(hwnd, ctypes.byref(rect))
            _diag('native_drag SetForegroundWindow=%d ReleaseCapture=%d GetWindowRect=%d rect=(%d,%d,%d,%d)',
                  fg, rel, got, rect.left, rect.top, rect.right, rect.bottom)
            send = user32.SendMessageW(hwnd, 0x00A1, 0x0002, 0)  # WM_NCLBUTTONDOWN, HTCAPTION
            _diag('native_drag SendMessageW returned=%d (should be 0 for modal loop)', send)
        except Exception as e:
            _diag('native_drag FAILED: %r', e)
            _dlog('Api.native_drag FAILED: %s', e)

    def custom_drag_begin(self) -> None:
        """Start a poll-driven window drag (DPI-safe, physical px).

        Replaces the WM_NCLBUTTONDOWN(HTCAPTION) trick, which a frameless
        WinForms/WebView2 window ignores (its WndProc never starts the caption
        move loop, so the window never moves). Here Python records the window
        rect + cursor in physical pixels, then a thread follows the cursor by
        SetWindowPos delta while the left button is held. JS only triggers it.
        Must be public: JS calls it through pywebview.api.custom_drag_begin().
        """
        _diag('custom_drag_begin entered active=%s', self._custom_drag_active)
        if self._custom_drag_active:
            return
        hwnd = _find_hwnd(self._title) or self._ensure_hwnd()
        if not hwnd:
            _diag('custom_drag_begin NO HWND')
            return
        class POINT(ctypes.Structure):
            _fields_ = [('x', ctypes.c_long), ('y', ctypes.c_long)]
        class RECT(ctypes.Structure):
            _fields_ = [('left', ctypes.c_long), ('top', ctypes.c_long),
                        ('right', ctypes.c_long), ('bottom', ctypes.c_long)]
        user32 = ctypes.windll.user32
        try:
            p0 = POINT()
            r0 = RECT()
            user32.GetCursorPos(ctypes.byref(p0))
            user32.GetWindowRect(hwnd, ctypes.byref(r0))
        except Exception as e:
            _diag('custom_drag_begin capture FAILED: %r', e)
            return
        _diag('custom_drag drag from cursor=(%d,%d) rect=(%d,%d,%d,%d)',
              p0.x, p0.y, r0.left, r0.top, r0.right, r0.bottom)
        stop = threading.Event()
        self._custom_drag_stop = stop
        self._custom_drag_active = True

        class POINT2(ctypes.Structure):
            _fields_ = [('x', ctypes.c_long), ('y', ctypes.c_long)]

        def loop():
            SWP_NOSIZE = 0x0001
            SWP_NOZORDER = 0x0004
            SWP_NOACTIVATE = 0x0010
            x0, y0 = p0.x, p0.y
            ox, oy = r0.left, r0.top
            prev = (x0, y0)
            n = 0
            try:
                while not stop.is_set():
                    # VK_LBUTTON (0x01) still held?
                    if not (user32.GetAsyncKeyState(0x01) & 0x8000):
                        break
                    time.sleep(0.008)
                    p = POINT2()
                    user32.GetCursorPos(ctypes.byref(p))
                    if (p.x, p.y) == prev:
                        continue
                    prev = (p.x, p.y)
                    dx, dy = p.x - x0, p.y - y0
                    user32.SetWindowPos(hwnd, 0, ox + dx, oy + dy,
                                        0, 0,
                                        SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)
                    n += 1
            except Exception as e:
                _diag('custom_drag loop FAILED: %r', e)
            finally:
                self._custom_drag_active = False
                _diag('custom_drag ended after %d moves', n)

        threading.Thread(target=loop, daemon=True).start()
        _diag('custom_drag_begin started thread')

    def custom_drag_end(self) -> None:
        """Signal the drag loop to stop (called from JS on mouseup)."""
        stop = getattr(self, '_custom_drag_stop', None)
        if stop:
            stop.set()
        self._custom_drag_active = False

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
