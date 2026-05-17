import json
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def _reload():
    import importlib
    import mdviewer
    importlib.reload(mdviewer)
    return mdviewer


class TestLoadConfig:
    def test_returns_defaults_when_missing(self, tmp_path):
        p = str(tmp_path / 'config.json')
        with patch('mdviewer.CONFIG_PATH', p):
            cfg = _reload().load_config()
        assert cfg['theme'] == 'dark'
        assert cfg['preset'] == 'github-dark'
        assert cfg['window']['width'] == 900

    def test_returns_defaults_on_corrupt_json(self, tmp_path):
        p = str(tmp_path / 'config.json')
        with open(p, 'w') as f:
            f.write('not json')
        with patch('mdviewer.CONFIG_PATH', p):
            cfg = _reload().load_config()
        assert cfg['theme'] == 'dark'

    def test_reads_saved_values(self, tmp_path):
        p = str(tmp_path / 'config.json')
        saved = {'theme': 'light', 'preset': 'github',
                 'window': {'width': 1200, 'height': 800, 'x': 100, 'y': 50}}
        with open(p, 'w') as f:
            json.dump(saved, f)
        with patch('mdviewer.CONFIG_PATH', p):
            cfg = _reload().load_config()
        assert cfg['theme'] == 'light'
        assert cfg['window']['width'] == 1200
        assert cfg['window']['x'] == 100

    def test_missing_window_key_uses_defaults(self, tmp_path):
        p = str(tmp_path / 'config.json')
        with open(p, 'w') as f:
            json.dump({'theme': 'light', 'preset': 'dracula'}, f)
        with patch('mdviewer.CONFIG_PATH', p):
            cfg = _reload().load_config()
        assert cfg['window']['width'] == 900


class TestSaveConfig:
    def test_creates_file_and_parent_dirs(self, tmp_path):
        p = str(tmp_path / 'sub' / 'config.json')
        with patch('mdviewer.CONFIG_PATH', p):
            _reload().save_config_file({'theme': 'dark', 'preset': 'dracula',
                                        'window': {'width': 900, 'height': 700, 'x': 0, 'y': 0}})
        assert os.path.exists(p)
        with open(p) as f:
            assert json.load(f)['preset'] == 'dracula'

    def test_overwrites_existing(self, tmp_path):
        p = str(tmp_path / 'config.json')
        with open(p, 'w') as f:
            json.dump({'theme': 'light'}, f)
        with patch('mdviewer.CONFIG_PATH', p):
            _reload().save_config_file({'theme': 'dark', 'preset': 'nord',
                                        'window': {'width': 800, 'height': 600, 'x': 0, 'y': 0}})
        with open(p) as f:
            assert json.load(f)['theme'] == 'dark'


class TestClampPosition:
    def test_none_inputs_return_none(self):
        import mdviewer
        assert mdviewer.clamp_position(None, None, 900, 700) == (None, None)

    def test_clamps_negative_to_zero(self):
        import mdviewer
        with patch('ctypes.windll.user32.GetSystemMetrics', side_effect=[1920, 1080]):
            x, y = mdviewer.clamp_position(-200, -100, 900, 700)
        assert x == 0 and y == 0

    def test_clamps_beyond_screen_right(self):
        import mdviewer
        with patch('ctypes.windll.user32.GetSystemMetrics', side_effect=[1920, 1080]):
            x, y = mdviewer.clamp_position(1500, 900, 900, 700)
        assert x == 1920 - 900
        assert y == 1080 - 700

    def test_valid_position_unchanged(self):
        import mdviewer
        with patch('ctypes.windll.user32.GetSystemMetrics', side_effect=[1920, 1080]):
            x, y = mdviewer.clamp_position(100, 50, 900, 700)
        assert x == 100 and y == 50
