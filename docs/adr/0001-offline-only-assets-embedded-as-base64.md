# Offline-only; JS/CSS assets embedded as base64 in source, not loaded at runtime

mdviewer has no intended network dependency — it must work fully offline, so
markdown-it and highlight.js (plus its theme CSS) are fetched once via the
dev-only `fetch_assets.py` and embedded as base64 strings in `assets.py`,
rather than loaded from a CDN at runtime. They're inlined in source rather
than shipped as separate files alongside the exe (which would also be
offline-safe) so the PyInstaller onefile build follows normal Python imports
from `mdviewer.py` with no extra `--add-data` for JS/CSS.

**Consequence:** upgrading markdown-it/highlight.js requires manually
re-running `fetch_assets.py` (which patches the sentinel block in `assets.py`)
and committing the diff, not bumping a version pin.
