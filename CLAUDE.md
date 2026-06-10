# CLAUDE.md — mdviewer

## What this is

Single-file Python markdown viewer for Windows 11. All app logic lives in `mdviewer.py`. No external assets at runtime — JS/CSS bundled as base64 strings.

## Commands

```bash
python mdviewer.py <file.md>   # run dev
pytest tests/                  # 16 tests
node tests/test_theme_cycle.mjs  # theme-cycle JS logic (extracted from template)
python fetch_assets.py         # re-embed JS/CSS (only needed after version bumps)
build.bat                      # PyInstaller → dist/mdviewer.exe
install.bat                    # register file association (HKCU, no admin)
```

Deploy after build:
```bash
cp dist/mdviewer.exe "$LOCALAPPDATA/mdviewer/mdviewer.exe"
```

Debug mode (writes `%APPDATA%\mdviewer\debug.log` + enables WebView2 DevTools):
```bash
MDVIEWER_DEBUG=1 python mdviewer.py test.md
```

## Critical constraints — read before editing

### 1. Underscore-prefix all non-API attributes on `Api`

pywebview's `get_functions()` (in `webview/util.py`) walks `dir(obj)` recursively, following any attribute whose object has `__module__`. Public attributes on `Api` are walked — if one resolves to a pywebview `Window`, pywebview recurses into the .NET WinForms control tree, throwing ~2.6 MB of COM exceptions per launch and making the UI sluggish.

**Rule:** every attribute on `Api` that is not a callable method must start with `_`.  
Current: `self._window`, `self._hwnd`, `self._title`, `self._md_path`.

The flip side: pywebview **never exposes underscore-prefixed methods to JS** (same `startswith('_')` filter). Any method JS must call (e.g. `refresh_resize_handles`, `force_activate`) has to be public. And every pywebview API call from JS returns a **Promise** — `await` it; truthiness checks on the raw return value silently pass.

### 2. Never use `window.screenX/Y` or `window.outerWidth/Height` for geometry

WebView2 in frameless mode returns 0 for `screenX/Y`. Use Win32 `GetWindowRect` (`_window_rect(hwnd)`) from Python for all position/size reads.

### 3. WS_THICKFRAME must be re-applied after fullscreen toggle

pywebview's `toggle_fullscreen()` restores `FormBorderStyle = None`, which strips `WS_THICKFRAME`. `Api.toggle_fullscreen()` calls `_enable_native_resize(hwnd)` after every toggle. Don't remove that call.

### 4. Snap uses fresh `FindWindowW` per call — not the cached `_hwnd`

`Api.snap()` calls `_find_hwnd(self._title)` fresh each time before `_work_area_for()`. Cached hwnd can become stale after style changes and return wrong monitor info, causing the "first click shifts window, second click works" glitch.

### 5. HTML template is one big string in `build_html()`

The entire HTML/CSS/JS page is a string in `build_html()` in `mdviewer.py`. Placeholders (`__THEME__`, `__PRESET__`, `__MARKDOWN_IT_JS__`, etc.) are filled via `.replace()` chains. When editing:
- Don't introduce strings that match placeholders unless intentional.
- Escape `{` / `}` not needed (we use `.replace()`, not `.format()`).
- Keep `__MARKDOWN_IT_JS__` and `__HLJS_JS__` as single tokens — they expand to ~100 KB each.

### 6. Asset bundle in `mdviewer.py`

`fetch_assets.py` patches the sentinel block between:
```
# -- ASSET BUNDLE ... ---
# -- END ASSET BUNDLE ---
```
Do not rename or reformat those comments. The regex in `fetch_assets.py` matches them exactly.

## Key functions

| Function | Purpose |
|----------|---------|
| `load_config()` / `save_config_file()` | Read/write `%APPDATA%\mdviewer\config.json` |
| `clamp_position(x, y, w, h)` | Clamp window pos to visible screen; returns `(None, None)` if inputs are None |
| `_find_hwnd(title)` | `FindWindowW` by title — use for snap; do NOT cache |
| `_window_rect(hwnd)` | `GetWindowRect` → `(x, y, w, h)` physical pixels |
| `_work_area_for(hwnd)` | `MonitorFromWindow` + `GetMonitorInfo` → workarea for current monitor |
| `_enable_native_resize(hwnd)` | Adds `WS_THICKFRAME` via `SetWindowLongW` + `SetWindowPos(FRAMECHANGED)` |
| `_get_required_window_size_for_client(cw, ch, hwnd)` | `AdjustWindowRectEx` → outer size for target client size |
| `build_html(config)` | Returns the full HTML page as a string |
| `Api.snap(mode)` | Snap window: `'left'`, `'right'`, `'reading'` |
| `Api.save_config(partial)` | Merge partial dict into config + persist window rect |
| `on_closing()` | Saves window rect via Win32 before destroy |
| `on_loaded()` | Calls `_enable_native_resize` after WebView2 load |

## Config schema

```json
{
  "theme": "dark | light",
  "preset": "github-dark | github | dracula | monokai | nord | atom-one-dark | solarized-dark | vs2015",
  "window": { "width": 900, "height": 700, "x": 200, "y": 150 }
}
```

Delete `%APPDATA%\mdviewer\config.json` to reset to defaults.

## Tests

```
tests/test_config.py        16 tests covering:
  - TestLoadConfig        (defaults, corrupt JSON, saved values, missing keys, 'system' theme survives load)
  - TestSaveConfig        (creates dirs, overwrites)
  - TestClampPosition     (None passthrough, negative, beyond-edge, valid, multi-monitor virtual screen)
  - TestDocWidthButtonAndSnapFlakiness  (centering math, fresh hwnd, AdjustWindowRectEx)
tests/test_theme_cycle.mjs  node test: extracts effectiveTheme()/nextTheme() from the
  JS template via THEME-CYCLE-LOGIC-START/END markers and verifies no theme click is
  a visual no-op under either OS appearance. Don't rename those markers.
```

Tests mock `ctypes.windll.user32` where needed. No real window required.

## Known platform quirks

- **Python 3.14 + pythonnet --pre**: stable, but required `--pre` flag to install. If pywebview install fails on a newer Python, try `pip install pythonnet --pre` first.
- **WinForms / Chromium backend**: pywebview picks `WinForms + Edge Chromium` on Windows. No CEF, no legacy EdgeHTML.
- **`FormBorderStyle.None`**: pywebview's frameless mode uses this .NET enum value. `None` is a Python keyword, so pywebview accesses it as `getattr(WinForms.FormBorderStyle, 'None')`.
- **File association**: registered under `HKCU\Software\Classes\Applications\mdviewer.exe` (not `.md` default override). Appears in "Open with" without stealing the default from other apps.
