# AGENTS.md — mdviewer

## Purpose

Windows 11 offline markdown viewer. Entry point `mdviewer.py` wires focused modules; JS/CSS embedded as base64. PyInstaller produces `dist/mdviewer.exe`.

## Ownership

| Path | Responsibility |
|------|----------------|
| `mdviewer.py` | Entry point: CLI/file dialog, window construction, file watcher, event wiring |
| `debug.py` | `_DEBUG`, `_dlog`, logging init (leaf — no app imports) |
| `assets.py` | Generated base64 bundle (`MARKDOWN_IT_JS`, `HLJS_JS`, `HLJS_THEMES`) |
| `config.py` | `CONFIG_PATH`, `DEFAULTS`, `PRESETS`, load/save, recent, encoding, version, OS dark theme |
| `geometry.py` | Win32 geometry, clamp, reading-width constants, `WS_THICKFRAME` helpers |
| `api.py` | pywebview `Api` bridge (JS-callable surface) |
| `template.py` | `build_html()` HTML/CSS/JS template string |
| `fetch_assets.py` | Dev-only CDN fetch → patch ASSET BUNDLE in `assets.py` |
| `build.bat` / `install.bat` | Package exe + HKCU file association |
| `tests/` | pytest + Node theme-cycle test — see `tests/AGENTS.md` |

## Local Contracts

### Config (`config.py`)

Schema keys in `DEFAULTS`: `theme`, `preset`, `window`, `recent`.  
`theme` may be `system` — never resolve to `dark`/`light` in `load_config` (only at paint time in `build_html` / JS).  
Config path: `%APPDATA%\mdviewer\config.json`, or `config.json` beside exe/script if present (portable mode).  
`window` x/y/width/height are **pywebview logical pixels** (not Win32 physical) — use `_geometry_from_window()` for persistence; keep `GetWindowRect` for snap math only.

### pywebview `Api` (`api.py`)

- Non-callable state on `Api` must be `_`-prefixed (`_window`, `_hwnd`, `_title`, `_md_path`, `_pre_fullscreen_rect`, `_geom_save_timer`).
- Methods JS calls must be public (`refresh_resize_handles`, `force_activate`, `snap`, …).
- pywebview API calls from JS return Promises — always `await`.

### Window geometry (`geometry.py`)

- Never use `window.screenX/Y` or `outerWidth/Height` in frameless WebView2.
- Snap/layout: fresh `_find_hwnd(title)` per call, not cached `_hwnd`.
- Re-apply `WS_THICKFRAME` after fullscreen and on focus (`_enable_native_resize`).

### HTML template (`template.py`)

- Lives in `build_html()` as one string; placeholders filled via `.replace()`.
- Theme-cycle logic between `THEME-CYCLE-LOGIC-START` / `END` — extracted by `tests/test_theme_cycle.mjs`.
- Asset constants imported from `assets.py`.

### Asset bundle (`assets.py`)

- Between `# -- ASSET BUNDLE` / `# -- END ASSET BUNDLE` — patched by `fetch_assets.py` only.
- Do not rename or reformat those sentinel comments.

### Doc-width snap

`btn-tall` → `Api.snap('reading')` — logical client width `_TARGET_READING_CLIENT_LOGICAL` (860px prose column + 48px `#page` padding per side → 956px box + scrollbar + outer margin), via `window.resize`/`move`.

## Work Guidance

- Prefer lightweight paths: `reloadFromDisk()` + `get_file()` for disk-backed reloads; avoid embedding large markdown in `evaluate_js`.
- File reads: `_read_text_file()` (utf-8-sig → utf-8 → cp1252).
- Version: dev uses `git rev-list --count`; frozen exe reads bundled `version.txt` from `build.bat`.
- Flat modules alongside `mdviewer.py` (not a package directory) — PyInstaller follows the local import graph from the entry script.
- Standing project principle: keep the app lean, minimal dependencies, no functionality for its own sake. Weigh new dependencies and abstractions against this before adding them. See `docs/adr/` for where this shaped specific decisions (asset bundling, config format).

## Verification

```bash
pytest tests/
node tests/test_theme_cycle.mjs
python -m py_compile mdviewer.py debug.py assets.py config.py geometry.py api.py template.py fetch_assets.py
```

## Child DOX Index

- `tests/AGENTS.md` — test layout and conventions
- `CONTEXT.md` — domain glossary (theme vs preset, snap, portable mode, recent files)
- `docs/adr/` — architecture decisions (offline asset embedding, frameless window, client-side rendering, file association)
