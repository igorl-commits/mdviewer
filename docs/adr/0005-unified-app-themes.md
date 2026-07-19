# Unified app themes (chrome + syntax); no dark/light/system mode

Appearance is a single **theme** key shared by page chrome and code
highlighting. The old split — `theme` as `dark`/`light`/`system` for chrome
only, plus an independent `preset` for highlight.js — is removed.

**Why:** Users expect picking “Dracula” (or Nord, etc.) to restyle the whole
viewer, not only fenced code. Independent light/dark chrome + dark code presets
produced mismatched looks and extra menu surface (cycle light/dark/system, then
pick a syntax theme).

**How it works:**

- Config `theme` is one of eight keys: `github-dark`, `github`, `dracula`,
  `monokai`, `nord`, `atom-one-dark`, `solarized-dark`, `vs2015` (default
  `github-dark`). Keys and labels live in `config.THEMES`.
- `template.py` defines chrome CSS variables per `[data-theme="…"]` (hand-authored
  palettes aligned with each highlight pack — not auto-parsed from HLJS CSS).
- The same key selects the highlight.js CSS string from `assets.HLJS_THEMES`
  into `#hljs-theme`.
- Gear/context menu lists **Theme** only; no light/dark/system cycle.
- No OS `prefers-color-scheme` follow mode.

**Migration:** On load, if the file still has legacy `theme` ∈
`{dark,light,system}` and a `preset` that is a valid app theme key, the preset
wins. Invalid/legacy theme alone falls back to `github-dark`. Saves never write
`preset`.

**Rejected alternatives:**

- Keep Theme + Preset independent (status quo) — too much UI, easy to get
  clashing chrome vs code.
- Infer chrome colors from HLJS CSS automatically — brittle contrast and
  incomplete menus/headings.
- Auto-apply HLJS stylesheets to the whole document — HLJS rules target
  `.hljs*` only; they do not define app chrome.
