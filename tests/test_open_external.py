"""Api.open_external must only hand http/https/mailto URLs to the OS."""
import ctypes
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if not hasattr(ctypes, 'windll'):  # allow importing api on non-Windows
    ctypes.windll = MagicMock()
from api import Api  # noqa: E402


@pytest.mark.parametrize('url', [
    'https://example.com/a?b=1', 'http://example.com', 'mailto:igor@example.com',
    'HTTPS://EXAMPLE.COM'])
def test_allowed_schemes_open(url):
    with patch('api.webbrowser.open', return_value=True) as op:
        assert Api('x.md', 'x').open_external(url) is True
    op.assert_called_once()


@pytest.mark.parametrize('url', [
    'javascript:alert(1)', 'file:///C:/Windows/System32/calc.exe', 'C:\\evil.exe',
    'ms-settings:', 'vbscript:x', 'data:text/html,hi', '', 'relative/page.md',
    'http://', None, 123, 'https://' + 'a' * 9000])
def test_other_schemes_refused(url):
    with patch('api.webbrowser.open') as op:
        assert Api('x.md', 'x').open_external(url) is False
    op.assert_not_called()


def test_template_intercepts_links():
    from template import build_html
    html = build_html({'theme': 'github-dark'})
    assert "closest('#content a[href]')" in html
    assert 'pywebview.api.open_external(href)' in html
    assert 'e.preventDefault();' in html
