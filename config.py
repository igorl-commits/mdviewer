"""Config load/save, portable path, recent files, version."""
import json
import os
import sys

if 'CONFIG_PATH' not in globals():
    # Portable mode: if config.json lives next to the exe/script, use it.
    # This is the only change needed for fully portable usage.
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0] if getattr(sys, 'frozen', False) else __file__))
    portable_config = os.path.join(exe_dir, 'config.json')
    if os.path.isfile(portable_config):
        CONFIG_PATH = portable_config
    else:
        CONFIG_PATH = os.path.join(os.environ.get('APPDATA', ''), 'mdviewer', 'config.json')


def _get_version() -> str:
    """Return '0.<N>' where N is the number of commits in the repo.

    Dev runs use git. Packaged exe reads version.txt (written by build.bat)
    or MDVIEWER_BUILD_VERSION if set.
    """
    if getattr(sys, 'frozen', False):
        ver = os.environ.get('MDVIEWER_BUILD_VERSION')
        if ver:
            return ver
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        try:
            with open(os.path.join(base, 'version.txt'), encoding='utf-8') as f:
                return f.read().strip()
        except OSError:
            pass
        return '0.34'
    try:
        import subprocess
        root = os.path.dirname(os.path.abspath(__file__))
        count = subprocess.check_output(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return f"0.{count}"
    except Exception:
        pass
    return '0.34'


APP_VERSION = _get_version()

# App appearance themes (chrome + matching highlight.js stylesheet key).
THEMES: list = [
    ('github-dark',    'GitHub Dark'),
    ('github',         'GitHub Light'),
    ('dracula',        'Dracula'),
    ('monokai',        'Monokai'),
    ('nord',           'Nord'),
    ('atom-one-dark',  'One Dark Pro'),
    ('solarized-dark', 'Solarized Dark'),
    ('vs2015',         'VS2015 Dark'),
]
THEME_KEYS = frozenset(k for k, _ in THEMES)

# Legacy aliases kept for any leftover imports during transition.
PRESETS = THEMES

DEFAULTS: dict = {
    'theme': 'github-dark',
    'window': {'width': 900, 'height': 700, 'x': None, 'y': None},
    'recent': [],
}

_LEGACY_UI_THEMES = frozenset({'dark', 'light', 'system'})


def _normalize_theme(raw_theme, legacy_preset=None) -> str:
    """Map config theme (and optional legacy preset) to a valid app theme key."""
    if raw_theme in THEME_KEYS:
        return raw_theme
    # Old schema: theme was dark|light|system, appearance lived in preset.
    if legacy_preset in THEME_KEYS:
        return legacy_preset
    if raw_theme in _LEGACY_UI_THEMES:
        return DEFAULTS['theme']
    return DEFAULTS['theme']


def load_config() -> dict:
    legacy_preset = None
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            data = {}
        legacy_preset = data.get('preset')
        config = {k: (v.copy() if isinstance(v, dict) else list(v) if isinstance(v, list) else v)
                    for k, v in DEFAULTS.items()}
        config.update({k: v for k, v in data.items() if k in DEFAULTS})
        config['window'] = dict(DEFAULTS['window'])
        config['window'].update(data.get('window', {}) or {})
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        config = {k: (v.copy() if isinstance(v, dict) else list(v) if isinstance(v, list) else v)
                    for k, v in DEFAULTS.items()}

    config['recent'] = list(config.get('recent', []))
    config['theme'] = _normalize_theme(config.get('theme'), legacy_preset)
    return config


def save_config_file(data: dict) -> None:
    parent = os.path.dirname(CONFIG_PATH)
    if parent:
        os.makedirs(parent, exist_ok=True)
    # Never persist removed keys (e.g. legacy preset) or invalid themes.
    out = {
        'theme': _normalize_theme(data.get('theme')),
        'window': data.get('window', DEFAULTS['window']),
        'recent': list(data.get('recent', [])),
    }
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)


def _read_text_file(path: str) -> str:
    """Read a text file: utf-8-sig → utf-8 → cp1252 fallback."""
    last_err = None
    for enc in ('utf-8-sig', 'utf-8', 'cp1252'):
        try:
            with open(path, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError as e:
            last_err = e
        except OSError:
            raise
    if last_err:
        raise last_err
    raise OSError(f'cannot read {path}')


def _update_recent_files(path: str, max_entries: int = 8) -> None:
    """Lightweight recent files tracking. Called on successful open."""
    try:
        cfg = load_config()
        recent = [p for p in cfg.get('recent', []) if p != path]
        recent.insert(0, path)
        cfg['recent'] = recent[:max_entries]
        save_config_file(cfg)
    except Exception:
        pass
