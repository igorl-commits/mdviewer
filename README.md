# mdviewer

Lightweight Windows 11 markdown viewer. Opens `.md` files natively via "Open with…". Frameless window, right-click theme switching, 8 syntax presets, persistent layout.

## Features

- **Open with** — register as a handler for `.md` files (no admin needed)
- **Frameless window** — no OS title bar; drag body to move, drag edges to resize
- **Right-click menu** — toggle light/dark + pick syntax theme on any file, any time
- **8 syntax presets** — GitHub Dark/Light, Dracula, Monokai, Nord, One Dark Pro, Solarized Dark, VS2015 Dark
- **Snap buttons** (hover top-right) — doc width, half-left, half-right, fullscreen
- **Persistent state** — window position/size, theme, preset saved on close
- **F11** — fullscreen toggle
- **Offline** — all JS/CSS assets bundled in the exe; no network needed

## Install

```bat
:: 1. Build (requires pyinstaller on PATH)
build.bat

:: 2. Register file association (HKCU only, no admin)
install.bat
```

After `install.bat`, right-click any `.md` → Open with → MD Viewer.

## Dev setup

```bash
pip install pywebview pyinstaller pytest
python fetch_assets.py        # download + embed JS/CSS into mdviewer.py (once)
python mdviewer.py test.md    # run without building exe
pytest tests/                 # 13 tests
```

Debug log: `set MDVIEWER_DEBUG=1` before launching — writes to `%APPDATA%\mdviewer\debug.log`.

## File structure

```
mdviewer.py        # entire app — single Python file
fetch_assets.py    # dev tool: downloads markdown-it + highlight.js, patches mdviewer.py
install.bat        # registers Windows file association
build.bat          # PyInstaller one-liner → dist/mdviewer.exe
tests/
  test_config.py   # unit tests (config layer, clamp, snap math)
test.md            # test file with code blocks in multiple languages
```

## Config

Stored at `%APPDATA%\mdviewer\config.json`:

```json
{
  "theme": "dark",
  "preset": "github-dark",
  "window": { "width": 900, "height": 700, "x": 200, "y": 150 }
}
```

Delete to reset to defaults.

## Architecture notes

- **pywebview 6.x + WinForms** — frameless window via `FormBorderStyle.None`. Native resize re-enabled post-creation by adding `WS_THICKFRAME` via `SetWindowLongW`.
- **API introspection trap** — pywebview's `get_functions()` recursively walks public attributes on the `js_api` object. All non-callable state must be underscore-prefixed (`self._window`, `self._hwnd`) or pywebview recurses into .NET objects and dumps ~2.6 MB of COM exceptions per launch.
- **Window geometry** — never trust `window.screenX/Y` in WebView2 frameless mode (returns 0). Use Win32 `GetWindowRect` + `MonitorFromWindow` for all position/snap logic.
- **Snap "doc width"** — uses `AdjustWindowRectEx` to convert target client width to outer window width, so thickframe borders don't eat the prose column.
- **Assets** — `fetch_assets.py` downloads markdown-it.js + highlight.js + 8 CSS themes from cdnjs and base64-encodes them into `mdviewer.py` as Python string literals. Fully offline after that.

## Stack

| Layer | Choice |
|-------|--------|
| Runtime | Python 3.12+, pywebview 6.x |
| Renderer | Edge WebView2 (built into Windows 11) |
| Markdown | markdown-it.js 13.x (bundled) |
| Syntax | highlight.js 11.x (bundled) |
| Packaging | PyInstaller `--onefile --noconsole` → ~21 MB |
| File assoc | HKCU registry, no admin |
