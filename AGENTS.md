# AGENTS.md — mdviewer

## Purpose

Windows 11 offline markdown viewer. Entry point `mdviewer.py` wires focused modules; JS/CSS embedded as base64. PyInstaller produces `dist/mdviewer.exe`.

## Ownership

| Path | Responsibility |
|------|----------------|
| `mdviewer.py` | Entry point: CLI/file dialog, window construction, file watcher, event wiring |
| `debug.py` | `_DEBUG`, `_dlog`, logging init (leaf — no app imports) |
| `assets.py` | Generated base64 bundle (`MARKDOWN_IT_JS`, `HLJS_JS`, `HLJS_THEMES`) |
| `config.py` | `CONFIG_PATH`, `DEFAULTS`, `THEMES`, load/save, recent, encoding, version |
| `geometry.py` | Win32 geometry, clamp, reading-width constants, `WS_THICKFRAME` helpers |
| `api.py` | pywebview `Api` bridge (JS-callable surface) |
| `template.py` | `build_html()` HTML/CSS/JS template string |
| `fetch_assets.py` | Dev-only CDN fetch → patch ASSET BUNDLE in `assets.py` |
| `build.bat` / `install.bat` | Package exe + HKCU file association |
| `tests/` | pytest + Node app-theme smoke test — see `tests/AGENTS.md` |

## Local Contracts

### Config (`config.py`)

Schema keys in `DEFAULTS`: `theme`, `window`, `recent`.  
`theme` is an **app theme** key (`github-dark`, `dracula`, …) — chrome + syntax colors together. Not `dark`/`light`/`system` (legacy values migrate via old `preset` if present).  
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
- App theme: `body[data-theme="<key>"]` chrome variables **and** HLJS CSS for the same key via `setTheme` (see ADR-0005).
- After render, relative `img` src resolved via `Api.resolve_media` → data URI (ADR-0006).
- Content images: thin `1px solid var(--border)` so dark screenshots don’t blend into chrome.
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
- Standing project principle: keep the app lean, minimal dependencies, no functionality for its own sake. Weigh new dependencies and abstractions against this before adding them. See `docs/adr/` for decisions (assets, frameless, client-side render, file association, unified themes, relative images).
- Domain language: use **Theme** as in `CONTEXT.md` (full app look). Do not reintroduce separate “preset” or dark/light/system UI modes without an ADR.

## Verification

```bash
pytest tests/
node tests/test_theme_cycle.mjs
python -m py_compile mdviewer.py debug.py assets.py config.py geometry.py api.py template.py fetch_assets.py
```

## Child DOX Index

- `tests/AGENTS.md` — test layout and conventions
- `CONTEXT.md` — domain glossary (theme, snap, portable mode, recent files)
- `docs/adr/` — architecture decisions:
  - `0001` offline asset embedding (`assets.py`)
  - `0002` frameless window
  - `0003` client-side markdown rendering
  - `0004` non-default file association
  - `0005` unified app themes (no dark/light/system)
  - `0006` relative images as data URIs
