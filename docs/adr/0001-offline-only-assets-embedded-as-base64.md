# Offline-only; JS/CSS assets embedded as base64 in source, not loaded at runtime

mdviewer has no intended network dependency — it must work fully offline, so
markdown-it and highlight.js (plus its theme CSS) are fetched once via the
dev-only `fetch_assets.py` and embedded as base64 strings directly in
`mdviewer.py`, rather than loaded from a CDN at runtime. They're inlined in
source rather than shipped as separate files alongside the exe (which would
also be offline-safe) to preserve the single-file distribution property:
`mdviewer.py` is the whole app in dev mode, and PyInstaller needs no
`--add-data` asset wiring to produce `dist/mdviewer.exe`.

**Consequence:** upgrading markdown-it/highlight.js requires manually
re-running `fetch_assets.py` and committing the diff, not bumping a version
pin.
