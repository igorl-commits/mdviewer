# mdviewer

An offline-only Windows markdown viewer (Python + pywebview). Config keys and UI controls use precise, distinct terms below — several look interchangeable but aren't.

## Language

**Theme**:
The UI appearance mode: `dark`, `light`, or `system` (follows OS appearance). Controls chrome and page background, not code block colors.
_Avoid_: Preset, color scheme, mode (when meaning code highlighting).

**Preset**:
The syntax-highlighting color scheme applied to code blocks (`github-dark`, `github`, `dracula`, `monokai`, `nord`, `atom-one-dark`, `solarized-dark`, `vs2015`). Independent of Theme — a light Theme can pair with a dark Preset.
_Avoid_: Theme, style, highlight theme.

**Snap**:
A window-placement command (`left`, `right`, `reading`) that resizes and repositions the frameless window via Win32 geometry, distinct from OS-native window snapping (Win+Arrow), which the frameless window doesn't participate in.
_Avoid_: Dock, tile.

**Reading width**:
The fixed logical client width (`_TARGET_READING_CLIENT_LOGICAL`) that `Snap('reading')` sizes the window to — a comfortable prose column width, not a percentage of the monitor like `left`/`right` snap.
_Avoid_: Reading mode (this app has no separate reading mode/view — it's a window size, not a display mode).

**Portable mode**:
An alternate config location: if `config.json` exists next to the exe/script, it's used instead of `%APPDATA%\mdviewer\config.json`. Activated by the presence of that file, not a setting or flag.
_Avoid_: Standalone mode, local config.

**Recent files**:
The `recent` list in config — file paths opened previously, persisted across sessions, distinct from the single currently-open file (`_md_path`).
