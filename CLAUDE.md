# CLAUDE.md — mdviewer

## What this is

Offline Python markdown viewer for Windows 11. Entry point `mdviewer.py` wires focused modules (`config`, `geometry`, `api`, `template`, `assets`, `debug`). No external assets at runtime — JS/CSS bundled as base64 in `assets.py`.

## Commands

```bash
python mdviewer.py <file.md>   # run dev
pytest tests/                  # unit tests (config, clamp, encoding, snap)
node tests/test_theme_cycle.mjs  # theme-cycle JS logic (extracted from template.py)
python fetch_assets.py         # re-embed JS/CSS into assets.py (only needed after version bumps)
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

### 1. Underscore-prefix all non-API attributes on `Api` (`api.py`)

pywebview's `get_functions()` (in `webview/util.py`) walks `dir(obj)` recursively, following any attribute whose object has `__module__`. Public attributes on `Api` are walked — if one resolves to a pywebview `Window`, pywebview recurses into the .NET WinForms control tree, throwing ~2.6 MB of COM exceptions per launch and making the UI sluggish.

**Rule:** every attribute on `Api` that is not a callable method must start with `_`.  
Current: `self._window`, `self._hwnd`, `self._title`, `self._md_path`, `self._pre_fullscreen_rect`, `self._geom_save_timer`.

The flip side: pywebview **never exposes underscore-prefixed methods to JS** (same `startswith('_')` filter). Any method JS must call (e.g. `refresh_resize_handles`, `force_activate`) has to be public. And every pywebview API call from JS returns a **Promise** — `await` it; truthiness checks on the raw return value silently pass.

### 2. Never use `window.screenX/Y` or `window.outerWidth/Height` for geometry

WebView2 in frameless mode returns 0 for `screenX/Y`. Use Win32 `GetWindowRect` (`_window_rect(hwnd)` in `geometry.py`) from Python for all position/size reads.

### 3. WS_THICKFRAME must be re-applied after fullscreen toggle

pywebview's `toggle_fullscreen()` restores `FormBorderStyle = None`, which strips `WS_THICKFRAME`. `Api.toggle_fullscreen()` calls `_enable_native_resize(hwnd)` after every toggle. Don't remove that call.

### 4. Snap uses fresh `FindWindowW` per call — not the cached `_hwnd`

`Api.snap()` calls `_find_hwnd(self._title)` fresh each time before `_work_area_for()`. Cached hwnd can become stale after style changes and return wrong monitor info, causing the "first click shifts window, second click works" glitch.

### 5. HTML template is one big string in `build_html()` (`template.py`)

The entire HTML/CSS/JS page is a string in `build_html()` in `template.py`. Placeholders (`__THEME__`, `__PRESET__`, `__MARKDOWN_IT_JS__`, etc.) are filled via `.replace()` chains. When editing:
- Don't introduce strings that match placeholders unless intentional.
- Escape `{` / `}` not needed (we use `.replace()`, not `.format()`).
- Keep `__MARKDOWN_IT_JS__` and `__HLJS_JS__` as single tokens — they expand to ~100 KB each.

### 6. Asset bundle in `assets.py`

`fetch_assets.py` patches the sentinel block between:
```
# -- ASSET BUNDLE ... ---
# -- END ASSET BUNDLE ---
```
Do not rename or reformat those comments. The regex in `fetch_assets.py` matches them exactly.

### 7. `debug.py` is a leaf module

`_DEBUG` / `_dlog` live in `debug.py` so `geometry` and `api` can import them without circular imports through `mdviewer`.

## Key functions

| Function | Module | Purpose |
|----------|--------|---------|
| `load_config()` / `save_config_file()` | `config` | Read/write config (`%APPDATA%\mdviewer\config.json` or portable `config.json` beside exe) |
| `_read_text_file(path)` | `config` | UTF-8-sig → UTF-8 → cp1252 file read |
| `clamp_position(x, y, w, h)` | `geometry` | Clamp window pos to virtual screen; returns `(None, None)` if inputs are None |
| `_find_hwnd(title)` | `geometry` | `FindWindowW` by title — use for snap; do NOT cache |
| `_window_rect(hwnd)` | `geometry` | `GetWindowRect` → `(x, y, w, h)` physical pixels |
| `_work_area_for(hwnd)` | `geometry` | `MonitorFromWindow` + `GetMonitorInfo` → workarea for current monitor |
| `_enable_native_resize(hwnd)` | `geometry` | Adds `WS_THICKFRAME` via `SetWindowLongW` + `SetWindowPos(FRAMECHANGED)` |
| `_get_required_window_size_for_client(cw, ch, hwnd)` | `geometry` | `AdjustWindowRectEx` → outer size for target client size |
| `_geometry_from_window(api)` | `geometry` | Logical-pixel window rect for config save/restore (not `GetWindowRect`) |
| `build_html(config)` | `template` | Returns the full HTML page as a string |
| `Api.snap(mode)` | `api` | Snap window: `'left'`, `'right'`, `'reading'` (reading uses logical px + pywebview resize) |
| `Api.save_config(partial)` | `api` | Merge partial dict into config + persist window rect |
| `main()` / `on_closing` / `on_loaded` | `mdviewer` | Entry wiring; save geometry on close; enable native resize after load |

## Config schema

```json
{
  "theme": "dark | light | system",
  "preset": "github-dark | github | dracula | monokai | nord | atom-one-dark | solarized-dark | vs2015",
  "window": { "width": 900, "height": 700, "x": 200, "y": 150 },
  "recent": []
}
```

Delete `%APPDATA%\mdviewer\config.json` to reset to defaults.

## Tests

```
tests/test_config.py        pytest: load/save config, recent preservation, clamp, snap math,
                            _read_text_file encoding, dead-code guards
tests/test_theme_cycle.mjs  node test: extracts effectiveTheme()/nextTheme() from the
  JS template in template.py via THEME-CYCLE-LOGIC-START/END markers and verifies no theme
  click is a visual no-op under either OS appearance. Don't rename those markers.
```

Tests mock `ctypes.windll.user32` where needed. No real window required.
Import paths follow modules (`config`, `geometry`, `api`) — no re-exports from `mdviewer`.

## Known platform quirks

- **Python 3.14 + pythonnet --pre**: stable, but required `--pre` flag to install. If pywebview install fails on a newer Python, try `pip install pythonnet --pre` first.
- **WinForms / Chromium backend**: pywebview picks `WinForms + Edge Chromium` on Windows. No CEF, no legacy EdgeHTML.
- **`FormBorderStyle.None`**: pywebview's frameless mode uses this .NET enum value. `None` is a Python keyword, so pywebview accesses it as `getattr(WinForms.FormBorderStyle, 'None')`.
- **File association**: registered under `HKCU\Software\Classes\Applications\mdviewer.exe` (not `.md` default override). Appears in "Open with" without stealing the default from other apps.

## Agent skills

### Issue tracker

Issues live as GitHub Issues in `igorl-commits/mdviewer`, managed via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`), unchanged. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context — one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
