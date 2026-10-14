"""Tests for config type validation, atomic writes and locked read-modify-write."""
import json
import os
import sys
import threading
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import config  # noqa: E402


@pytest.fixture
def cfg_path(tmp_path):
    p = str(tmp_path / 'sub' / 'config.json')
    with patch('config.CONFIG_PATH', p):
        yield p


def _write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(data if isinstance(data, str) else json.dumps(data))


# -- (3) type validation ------------------------------------------------------

@pytest.mark.parametrize('window', [[1, 2], 'big', 42, None, True])
def test_non_dict_window_falls_back(cfg_path, window):
    _write(cfg_path, {'window': window})
    assert config.load_config()['window'] == config.DEFAULTS['window']


@pytest.mark.parametrize('bad', ['900', None, True, -5, 0, float('nan'), [1]])
def test_bad_width_height_fall_back(cfg_path, bad):
    raw = '{"window": {"width": %s, "height": %s}}' % (
        'NaN' if bad != bad else json.dumps(bad), 'NaN' if bad != bad else json.dumps(bad))
    _write(cfg_path, raw)
    w = config.load_config()['window']
    assert w['width'] == 900 and w['height'] == 700


def test_bad_xy_become_none_and_floats_truncate(cfg_path):
    _write(cfg_path, {'window': {'width': 1000.7, 'height': 800, 'x': 'left', 'y': 12.9}})
    w = config.load_config()['window']
    assert w == {'width': 1000, 'height': 800, 'x': None, 'y': 12}


def test_unknown_window_keys_dropped(cfg_path):
    _write(cfg_path, {'window': {'width': 1000, 'height': 800, 'evil': 1}})
    assert 'evil' not in config.load_config()['window']


@pytest.mark.parametrize('recent', ['C:/a.md', {'a': 1}, 5, None])
def test_non_list_recent_falls_back(cfg_path, recent):
    _write(cfg_path, {'recent': recent})
    assert config.load_config()['recent'] == []


def test_recent_drops_non_strings(cfg_path):
    _write(cfg_path, {'recent': ['a.md', 3, None, '', 'b.md', ['x']]})
    assert config.load_config()['recent'] == ['a.md', 'b.md']


@pytest.mark.parametrize('theme', [123, ['nord'], {'k': 1}, 'nope', None])
def test_bad_theme_falls_back(cfg_path, theme):
    _write(cfg_path, {'theme': theme})
    assert config.load_config()['theme'] == 'github-dark'


@pytest.mark.parametrize('raw', ['[1,2,3]', '"str"', 'null', '\xff\xfe garbage'])
def test_non_object_or_garbage_root(cfg_path, raw):
    _write(cfg_path, raw)
    assert config.load_config() == config._defaults()


def test_valid_config_roundtrips(cfg_path):
    data = {'theme': 'nord', 'recent': ['a.md'],
            'window': {'width': 1200, 'height': 900, 'x': -1900, 'y': 10}}
    _write(cfg_path, data)
    assert config.load_config() == data


# -- (2) atomic write ------------------------------------------------------------

def test_save_is_atomic_and_leaves_no_tmp(cfg_path):
    config.save_config_file({'theme': 'nord'})
    assert json.load(open(cfg_path))['theme'] == 'nord'
    assert not os.path.exists(cfg_path + '.tmp')


def test_failed_write_keeps_old_file(cfg_path):
    config.save_config_file({'theme': 'nord', 'recent': ['keep.md']})
    with patch('config.json.dump', side_effect=RuntimeError('disk full')):
        with pytest.raises(RuntimeError):
            config.save_config_file({'theme': 'dracula'})
    assert config.load_config()['recent'] == ['keep.md']
    assert config.load_config()['theme'] == 'nord'
    assert not os.path.exists(cfg_path + '.tmp')


def test_save_validates_window(cfg_path):
    config.save_config_file({'window': 'junk'})
    assert config.load_config()['window'] == config.DEFAULTS['window']


# -- (2) locking ---------------------------------------------------------------

def test_concurrent_updates_do_not_lose_writes(cfg_path):
    """Recent-file updates racing geometry saves must all survive."""
    n = 40
    paths = [f'f{i}.md' for i in range(n)]
    errors = []

    def add_recent(p):
        try:
            config._update_recent_files(p, max_entries=1000)
        except Exception as e:  # pragma: no cover
            errors.append(e)

    def save_geom(i):
        def m(c):
            c['window'] = {'width': 500 + i, 'height': 400, 'x': 0, 'y': 0}
        try:
            config.update_config(m)
        except Exception as e:  # pragma: no cover
            errors.append(e)

    threads = [threading.Thread(target=add_recent, args=(p,)) for p in paths]
    threads += [threading.Thread(target=save_geom, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert sorted(config.load_config()['recent']) == sorted(paths)


def test_update_config_holds_lock(cfg_path):
    seen = []
    config.update_config(lambda c: seen.append(config.CONFIG_LOCK._is_owned()))
    assert seen == [True]
