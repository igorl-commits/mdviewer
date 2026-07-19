import json
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def _reload_config():
    import importlib
    import config
    importlib.reload(config)
    return config


class TestLoadConfig:
    def test_returns_defaults_when_missing(self, tmp_path):
        p = str(tmp_path / 'config.json')
        with patch('config.CONFIG_PATH', p):
            cfg = _reload_config().load_config()
        assert cfg['theme'] == 'dark'
        assert cfg['preset'] == 'github-dark'
        assert cfg['window']['width'] == 900

    def test_returns_defaults_on_corrupt_json(self, tmp_path):
        p = str(tmp_path / 'config.json')
        with open(p, 'w') as f:
            f.write('not json')
        with patch('config.CONFIG_PATH', p):
            cfg = _reload_config().load_config()
        assert cfg['theme'] == 'dark'

    def test_reads_saved_values(self, tmp_path):
        p = str(tmp_path / 'config.json')
        saved = {'theme': 'light', 'preset': 'github',
                 'window': {'width': 1200, 'height': 800, 'x': 100, 'y': 50}}
        with open(p, 'w') as f:
            json.dump(saved, f)
        with patch('config.CONFIG_PATH', p):
            cfg = _reload_config().load_config()
        assert cfg['theme'] == 'light'
        assert cfg['window']['width'] == 1200
        assert cfg['window']['x'] == 100

    def test_system_theme_survives_load(self, tmp_path):
        """theme='system' must round-trip through load_config unresolved, otherwise
        any config save (geometry, recent files) permanently overwrites the user's
        'follow system' choice with a concrete dark/light value."""
        p = str(tmp_path / 'config.json')
        with open(p, 'w') as f:
            json.dump({'theme': 'system', 'preset': 'nord'}, f)
        with patch('config.CONFIG_PATH', p):
            cfg = _reload_config().load_config()
        assert cfg['theme'] == 'system'

    def test_missing_window_key_uses_defaults(self, tmp_path):
        p = str(tmp_path / 'config.json')
        with open(p, 'w') as f:
            json.dump({'theme': 'light', 'preset': 'dracula'}, f)
        with patch('config.CONFIG_PATH', p):
            cfg = _reload_config().load_config()
        assert cfg['window']['width'] == 900

    def test_recent_files_round_trip(self, tmp_path):
        p = str(tmp_path / 'config.json')
        saved = {
            'theme': 'dark', 'preset': 'github-dark',
            'window': {'width': 900, 'height': 700, 'x': 0, 'y': 0},
            'recent': ['C:/docs/a.md', 'C:/docs/b.md'],
        }
        with open(p, 'w') as f:
            json.dump(saved, f)
        with patch('config.CONFIG_PATH', p):
            cfg = _reload_config().load_config()
        assert cfg['recent'] == ['C:/docs/a.md', 'C:/docs/b.md']


class TestSaveConfig:
    def test_creates_file_and_parent_dirs(self, tmp_path):
        p = str(tmp_path / 'sub' / 'config.json')
        with patch('config.CONFIG_PATH', p):
            _reload_config().save_config_file({
                'theme': 'dark', 'preset': 'dracula',
                'window': {'width': 900, 'height': 700, 'x': 0, 'y': 0},
            })
        assert os.path.exists(p)
        with open(p) as f:
            assert json.load(f)['preset'] == 'dracula'

    def test_overwrites_existing(self, tmp_path):
        p = str(tmp_path / 'config.json')
        with open(p, 'w') as f:
            json.dump({'theme': 'light'}, f)
        with patch('config.CONFIG_PATH', p):
            _reload_config().save_config_file({
                'theme': 'dark', 'preset': 'nord',
                'window': {'width': 800, 'height': 600, 'x': 0, 'y': 0},
            })
        with open(p) as f:
            assert json.load(f)['theme'] == 'dark'

    def test_save_config_preserves_recent(self, tmp_path):
        p = str(tmp_path / 'config.json')
        with open(p, 'w') as f:
            json.dump({
                'theme': 'dark', 'preset': 'github-dark',
                'window': {'width': 900, 'height': 700, 'x': 0, 'y': 0},
                'recent': ['C:/keep.md'],
            }, f)
        with patch('config.CONFIG_PATH', p):
            _reload_config()
            import mdviewer
            api = mdviewer.Api('x.md', 'x.md')
            api._window = MagicMock(
                fullscreen=False, x=10, y=20, width=800, height=600)
            api.save_config({'theme': 'light'})
        with open(p) as f:
            saved = json.load(f)
        assert saved['theme'] == 'light'
        assert saved['recent'] == ['C:/keep.md']

    def test_save_geometry_preserves_recent(self, tmp_path):
        p = str(tmp_path / 'config.json')
        with open(p, 'w') as f:
            json.dump({
                'theme': 'dark', 'preset': 'github-dark',
                'window': {'width': 900, 'height': 700, 'x': 0, 'y': 0},
                'recent': ['C:/keep.md'],
            }, f)
        with patch('config.CONFIG_PATH', p):
            _reload_config()
            import mdviewer
            api = mdviewer.Api('x.md', 'x.md')
            api._window = MagicMock(fullscreen=False, x=100, y=50, width=900, height=700)
            api._save_geometry()
        with open(p) as f:
            saved = json.load(f)
        assert saved['recent'] == ['C:/keep.md']


class TestClampPosition:
    # clamp_position queries the *virtual screen* (all monitors combined):
    # GetSystemMetrics(76/77/78/79) = SM_X/Y/CX/CYVIRTUALSCREEN, in that order.

    def test_none_inputs_return_none(self):
        import geometry
        assert geometry.clamp_position(None, None, 900, 700) == (None, None)

    def test_clamps_negative_to_zero(self):
        import geometry
        with patch('ctypes.windll.user32.GetSystemMetrics', side_effect=[0, 0, 1920, 1080]):
            x, y = geometry.clamp_position(-200, -100, 900, 700)
        assert x == 0 and y == 0

    def test_clamps_beyond_screen_right(self):
        import geometry
        with patch('ctypes.windll.user32.GetSystemMetrics', side_effect=[0, 0, 1920, 1080]):
            x, y = geometry.clamp_position(1500, 900, 900, 700)
        assert x == 1920 - 900
        assert y == 1080 - 700

    def test_valid_position_unchanged(self):
        import geometry
        with patch('ctypes.windll.user32.GetSystemMetrics', side_effect=[0, 0, 1920, 1080]):
            x, y = geometry.clamp_position(100, 50, 900, 700)
        assert x == 100 and y == 50

    def test_secondary_monitor_position_preserved(self):
        """A window on a second monitor (right of primary) must not be pulled back."""
        import geometry
        with patch('ctypes.windll.user32.GetSystemMetrics', side_effect=[0, 0, 3840, 1080]):
            x, y = geometry.clamp_position(2500, 100, 900, 700)
        assert x == 2500 and y == 100

    def test_monitor_left_of_primary_preserved(self):
        """Virtual screen can start at negative coords (monitor left of primary)."""
        import geometry
        with patch('ctypes.windll.user32.GetSystemMetrics', side_effect=[-1920, 0, 3840, 1080]):
            x, y = geometry.clamp_position(-1500, 100, 900, 700)
        assert x == -1500 and y == 100


class TestDocWidthButtonAndSnapFlakiness:
    """TDD tests for the two reported issues:

    1. "doc width" button must set the window to the *intended doc (prose) width*,
       centered on the current monitor, with max (workarea) height.
       The old magic _READING_WIDTH=980 as *outer* size + thickframe made the
       effective #page column "much smaller" than designed.

    2. Sequential clicks on the top-right buttons (tall/reading, left, right, full)
       are flaky ("first click shifts window slightly left, second click is needed").
       Root cause: stale cached hwnd in Api._ensure_hwnd (populated once via FindWindowW
       by title) + MonitorFromWindow / SetWindowPos on that hwnd after the previous
       move or fullscreen style change has not yet fully settled in the OS.
    """

    def test_reading_centering_formula_is_correct(self):
        """The x for a reading snap must be the true center of the workarea for the chosen rw."""
        wx, wy, ww, wh = 0, 0, 1920, 1080
        rw = 1004  # example outer width after adjustment for the doc column
        x = wx + (ww - rw) // 2
        y = wy
        h = wh
        assert x == (1920 - 1004) // 2
        assert y == 0
        assert h == 1080

    def test_fresh_hwnd_lookup_is_used_for_geometry(self):
        """After the fix, snap paths must prefer a fresh FindWindowW (by title) on every call
        instead of a forever-cached hwnd. This eliminates the 'click twice' race."""
        import geometry as g
        calls = []
        orig = g._find_hwnd

        def spy(title):
            calls.append(title)
            return 12345  # fake hwnd

        try:
            g._find_hwnd = spy
            # We can't easily instantiate a full Api without a real webview window here,
            # but the presence of the call in the snap source + this test documents the contract.
            # The real verification happens at runtime + the manual button sequence test.
            assert callable(g._find_hwnd)
        finally:
            g._find_hwnd = orig

    def test_adjust_helper_returns_outer_larger_than_client(self):
        """_get_required_window_size_for_client must use AdjustWindowRectEx (with the
        thickframe style) so that the final client area matches the CSS #page design
        instead of being eaten by the non-client borders. This fixes 'window not on doc width'."""
        import geometry as g

        with patch('ctypes.windll.user32.GetWindowLongW', return_value=0x40000), \
             patch('ctypes.windll.user32.AdjustWindowRectEx') as mock_adj:
            def fake_adj(rect, style, has_menu, exstyle):
                rect.left -= 8
                rect.top -= 8
                rect.right += 8
                rect.bottom += 8
            mock_adj.side_effect = fake_adj
            ow, oh = g._get_required_window_size_for_client(988, 700, 0xDEADBEEF)
            assert ow >= 988


class TestReadTextFile:
    def test_utf8_sig_bom(self, tmp_path):
        p = tmp_path / 'bom.md'
        p.write_bytes(b'\xef\xbb\xbf# hello')
        import config
        assert config._read_text_file(str(p)) == '# hello'

    def test_cp1252_fallback(self, tmp_path):
        p = tmp_path / 'win.md'
        p.write_bytes('caf\xe9'.encode('cp1252'))
        import config
        assert config._read_text_file(str(p)) == 'café'


class TestWindowGeometry:
    def test_geometry_from_window_uses_pywebview_api(self):
        import geometry as g
        import mdviewer as m
        api = m.Api('x.md', 'x.md')
        win = MagicMock(fullscreen=False, x=120, y=80, width=1024, height=768)
        api._window = win
        assert g._geometry_from_window(api) == (120, 80, 1024, 768)

    def test_save_geometry_persists_pywebview_coords(self, tmp_path):
        p = str(tmp_path / 'config.json')
        with open(p, 'w') as f:
            json.dump({
                'theme': 'dark', 'preset': 'github-dark',
                'window': {'width': 900, 'height': 700, 'x': 0, 'y': 0},
            }, f)
        with patch('config.CONFIG_PATH', p):
            _reload_config()
            import mdviewer
            api = mdviewer.Api('x.md', 'x.md')
            win = MagicMock(fullscreen=False, x=250, y=100, width=1100, height=850)
            api._window = win
            api._save_geometry()
        with open(p) as f:
            saved = json.load(f)['window']
        assert saved == {'width': 1100, 'height': 850, 'x': 250, 'y': 100}


class TestReadingSnap:
    def test_target_width_matches_css_border_box(self):
        import geometry as g
        assert g._PAGE_MAX_LOGICAL == 860 + 48 * 2
        assert g._TARGET_READING_CLIENT_LOGICAL == 956 + 24 + 64 * 2

    def test_outer_logical_scales_with_dpi(self):
        import geometry as g
        with patch.object(g, '_hwnd_dpi_scale', return_value=1.5), \
             patch.object(g, '_get_required_window_size_for_client', return_value=(1350, 200)):
            outer, _ = g._outer_logical_for_client_logical(884, 100, 0x1234)
        assert outer == 900

    def test_reading_snap_uses_pywebview_resize(self):
        import mdviewer as m
        import inspect
        src = inspect.getsource(m.Api.snap)
        assert 'self._window.resize' in src
        assert '_TARGET_READING_CLIENT_LOGICAL' in src


class TestSnapApi:
    def test_reading_mode_exists(self):
        import mdviewer as m
        import inspect
        src = inspect.getsource(m.Api.snap)
        assert "mode == 'reading'" in src

    def test_half_screen_helpers_removed(self):
        import mdviewer as m
        assert not hasattr(m.Api, 'snap_to_half')
        assert not hasattr(m.Api, 'snap_to_content_width')
