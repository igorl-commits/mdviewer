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

from geometry import (
    _GWL_EXSTYLE,
    _GWL_STYLE,
    _MONITORINFO,
    _PAGE_CONTENT_LOGICAL,
    _PAGE_HPAD_LOGICAL,
    _PAGE_MAX_LOGICAL,
    _POINT,
    _READING_SIDE_MARGIN_LOGICAL,
    _RECT,
    _SCROLLBAR_GUTTER_LOGICAL,
    _SWP_FRAMECHANGED,
    _TARGET_READING_CLIENT_LOGICAL,
    _WS_THICKFRAME,
    _cursor_pos,
    _enable_native_resize,
    _find_hwnd,
    _geometry_from_window,
    _get_required_window_size_for_client,
    _hwnd_dpi_scale,
    _logical_work_area_for,
    _outer_logical_for_client_logical,
    _window_rect,
    _work_area_for,
    clamp_position,
)

from api import Api

from template import build_html

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
