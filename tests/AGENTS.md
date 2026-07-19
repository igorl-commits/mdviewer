# AGENTS.md — tests/

## Purpose

Unit and extracted-JS tests for mdviewer. No real WebView window required.

## Ownership

| File | Covers |
|------|--------|
| `test_config.py` | `config` load/save, `geometry.clamp_position`, snap math, `_read_text_file`, `_geometry_from_window`, `api.Api` config preservation |
| `test_theme_cycle.mjs` | All 8 app themes have chrome CSS; no legacy light/dark/system cycle |

## Local Contracts

- Patch `config.CONFIG_PATH` and `importlib.reload(config)` when testing config (module-level `CONFIG_PATH`).
- Import symbols from their owning modules (`config`, `geometry`, `api`) — no re-exports from `mdviewer`.
- Mock `ctypes.windll.user32` for geometry tests.
- App theme keys live in `config.THEMES` and matching `[data-theme="…"]` rules in `template.py`.

## Verification

```bash
pytest tests/ -v
node tests/test_theme_cycle.mjs
```

## Child DOX Index

(none)
