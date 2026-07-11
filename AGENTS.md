# AGENTS.md — mdviewer

## Purpose

Single-file Windows 11 markdown viewer (`mdviewer.py`). Offline runtime: JS/CSS embedded as base64. PyInstaller produces `dist/mdviewer.exe`.

## Ownership

| Path | Responsibility |
|------|----------------|
| `mdviewer.py` | App logic, HTML template, Win32 geometry, `Api` bridge |
| `fetch_assets.py` | Dev-only CDN fetch → patch ASSET BUNDLE in `mdviewer.py` |
| `build.bat` / `install.bat` | Package exe + HKCU file association |
| `tests/` | pytest + Node theme-cycle test — see `tests/AGENTS.md` |

## Local Contracts

### Config (`load_config` / `save_config_file`)

Schema keys in `DEFAULTS`: `theme`, `preset`, `window`, `recent`.  
`theme` may be `system` — never resolve to `dark`/`light` in `load_config` (only at paint time in `build_html` / JS).  
Config path: `%APPDATA%\mdviewer\config.json`, or `config.json` beside exe/script if present (portable mode).  
`window` x/y/width/height are **pywebview logical pixels** (not Win32 physical) — use `_geometry_from_window()` for persistence; keep `GetWindowRect` for snap math only.

### pywebview `Api`

- Non-callable state on `Api` must be `_`-prefixed (`_window`, `_hwnd`, `_title`, `_md_path`).
- Methods JS calls must be public (`refresh_resize_handles`, `force_activate`, `snap`, …).
- pywebview API calls from JS return Promises — always `await`.

### Window geometry

- Never use `window.screenX/Y` or `outerWidth/Height` in frameless WebView2.
- Snap/layout: fresh `_find_hwnd(title)` per call, not cached `_hwnd`.
- Re-apply `WS_THICKFRAME` after fullscreen and on focus (`_enable_native_resize`).

### HTML template

- Lives in `build_html()` as one string; placeholders filled via `.replace()`.
- Theme-cycle logic between `THEME-CYCLE-LOGIC-START` / `END` — extracted by `tests/test_theme_cycle.mjs`.
- Asset bundle between `# -- ASSET BUNDLE` / `# -- END ASSET BUNDLE` — patched by `fetch_assets.py` only.

### Doc-width snap

`btn-tall` → `Api.snap('reading')` — logical client width `_TARGET_READING_CLIENT_LOGICAL` (860px prose column + 48px `#page` padding per side → 956px box + scrollbar + outer margin), via `window.resize`/`move`.

## Work Guidance

- Prefer lightweight paths: `reloadFromDisk()` + `get_file()` for disk-backed reloads; avoid embedding large markdown in `evaluate_js`.
- File reads: `_read_text_file()` (utf-8-sig → utf-8 → cp1252).
- Version: dev uses `git rev-list --count`; frozen exe reads bundled `version.txt` from `build.bat`.

## Verification

```bash
pytest tests/
node tests/test_theme_cycle.mjs
python -m py_compile mdviewer.py fetch_assets.py
```

## Child DOX Index

- `tests/AGENTS.md` — test layout and conventions