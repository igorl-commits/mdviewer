"""Config load/save, portable path, recent files, version, app theme keys."""
import json
import os
import sys
import threading

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
    """Return the app release version (currently '1.0').

    Packaged exe may override via version.txt (written by build.bat) or the
    MDVIEWER_BUILD_VERSION env var; dev runs report the release version.
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
    return '1.0'


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

# Guards every read-modify-write of the config file. Re-entrant so a helper
# holding it can call load_config/save_config_file.
CONFIG_LOCK = threading.RLock()


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


def _defaults() -> dict:
    return {k: (v.copy() if isinstance(v, dict) else list(v) if isinstance(v, list) else v)
            for k, v in DEFAULTS.items()}


def _num(value, default, minimum=None):
    """Return value as int if it is a real finite number, else default."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    if value != value or value in (float('inf'), float('-inf')):
        return default
    value = int(value)
    if minimum is not None and value < minimum:
        return default
    return value


def _validate_window(raw) -> dict:
    d = DEFAULTS['window']
    if not isinstance(raw, dict):
        return dict(d)
    return {
        'width':  _num(raw.get('width'), d['width'], minimum=1),
        'height': _num(raw.get('height'), d['height'], minimum=1),
        'x': None if raw.get('x') is None else _num(raw.get('x'), None),
        'y': None if raw.get('y') is None else _num(raw.get('y'), None),
    }


def _validate_recent(raw) -> list:
    if not isinstance(raw, list):
        return []
    return [p for p in raw if isinstance(p, str) and p]


def load_config() -> dict:
    with CONFIG_LOCK:
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError, OSError):
            data = {}
    if not isinstance(data, dict):
        data = {}
    config = _defaults()
    config['window'] = _validate_window(data.get('window'))
    config['recent'] = _validate_recent(data.get('recent'))
    raw_theme = data.get('theme') if isinstance(data.get('theme'), str) else None
    legacy = data.get('preset') if isinstance(data.get('preset'), str) else None
    config['theme'] = _normalize_theme(raw_theme, legacy)
    return config


def save_config_file(data: dict) -> None:
    """Atomically write config (tmp file + os.replace) under CONFIG_LOCK."""
    out = {
        'theme': _normalize_theme(data.get('theme')),
        'window': _validate_window(data.get('window', DEFAULTS['window'])),
        'recent': _validate_recent(data.get('recent', [])),
    }
    with CONFIG_LOCK:
        parent = os.path.dirname(CONFIG_PATH)
        if parent:
            os.makedirs(parent, exist_ok=True)
        tmp = CONFIG_PATH + '.tmp'
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(out, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, CONFIG_PATH)
        except BaseException:
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise


def update_config(mutate) -> dict:
    """Locked read-modify-write: mutate(cfg) edits a fresh load, then saves."""
    with CONFIG_LOCK:
        cfg = load_config()
        mutate(cfg)
        save_config_file(cfg)
        return cfg


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
    def _mutate(cfg):
        recent = [p for p in cfg.get('recent', []) if p != path]
        recent.insert(0, path)
        cfg['recent'] = recent[:max_entries]
    try:
        update_config(_mutate)
    except Exception:
        pass
