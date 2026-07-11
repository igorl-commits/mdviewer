# AGENTS.md — tests/

## Purpose

Unit and extracted-JS tests for mdviewer. No real WebView window required.

## Ownership

| File | Covers |
|------|--------|
| `test_config.py` | `load_config`, `save_config_file`, `clamp_position`, snap math, `_read_text_file`, `_geometry_from_window`, `Api` config preservation |
| `test_theme_cycle.mjs` | `effectiveTheme()` / `nextTheme()` from template markers — no visual no-op on theme click |

## Local Contracts

- Patch `mdviewer.CONFIG_PATH` and `importlib.reload(mdviewer)` when testing config (module-level `CONFIG_PATH`).
- Mock `ctypes.windll.user32` for geometry tests.
- Do not rename `THEME-CYCLE-LOGIC-START` / `END` in `mdviewer.py` without updating the Node test.

## Verification

```bash
pytest tests/ -v
node tests/test_theme_cycle.mjs
```

## Child DOX Index

(none)