"""Win32 window geometry, reading-width constants, clamp helpers."""
import ctypes

from debug import _dlog

def clamp_position(x, y, width: int, height: int):
    """Return (x, y) clamped to the virtual screen (all monitors combined);
    (None, None) if inputs are None. Using SM_*VIRTUALSCREEN instead of the
    primary-monitor metrics keeps windows restored on secondary monitors."""
    if x is None or y is None:
        return None, None
    try:
        user32 = ctypes.windll.user32
        vx = user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
        vy = user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
        vw = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
        vh = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
        x = max(vx, min(int(x), vx + vw - width))
        y = max(vy, min(int(y), vy + vh - height))
    except Exception:
        return 0, 0
    return x, y


class _RECT(ctypes.Structure):
    _fields_ = [('left', ctypes.c_long), ('top', ctypes.c_long),
                ('right', ctypes.c_long), ('bottom', ctypes.c_long)]


class _POINT(ctypes.Structure):
    _fields_ = [('x', ctypes.c_long), ('y', ctypes.c_long)]


def _find_hwnd(title: str):
    return ctypes.windll.user32.FindWindowW(None, title) or None


def _window_rect(hwnd):
    r = _RECT()
    if hwnd and ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r)):
        return r.left, r.top, r.right - r.left, r.bottom - r.top
    return None


def _cursor_pos():
    p = _POINT()
    if ctypes.windll.user32.GetCursorPos(ctypes.byref(p)):
        return p.x, p.y
    return None


# Win32 constants for restoring native resize on a frameless window
_GWL_STYLE = -16
_GWL_EXSTYLE = -20
_WS_THICKFRAME = 0x00040000
# SWP_NOMOVE|NOSIZE|NOZORDER|NOACTIVATE|FRAMECHANGED — force a non-client redraw
_SWP_FRAMECHANGED = 0x0001 | 0x0002 | 0x0004 | 0x0010 | 0x0020


class _MONITORINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize',   ctypes.c_uint32),
        ('rcMonitor', _RECT),
        ('rcWork',    _RECT),  # excludes taskbar
        ('dwFlags',   ctypes.c_uint32),
    ]


def _work_area_for(hwnd):
    """Work-area (excludes taskbar) of the monitor that contains the window."""
    if not hwnd:
        return None
    user32 = ctypes.windll.user32
    hmon = user32.MonitorFromWindow(hwnd, 2)  # MONITOR_DEFAULTTONEAREST
    if not hmon:
        return None
    mi = _MONITORINFO()
    mi.cbSize = ctypes.sizeof(_MONITORINFO)
    if user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
        r = mi.rcWork
        return r.left, r.top, r.right - r.left, r.bottom - r.top
    return None


def _get_required_window_size_for_client(client_w: int, client_h: int, hwnd: int):
    """Return (outer_w, outer_h) such that the window's *client* area will be
    at least (client_w, client_h) after the OS applies the current thickframe
    and other non-client borders.

    This is the key to making the "doc width" button actually deliver the
    designed prose column width instead of a "much smaller" area.
    """
    if not hwnd:
        return client_w, client_h
    try:
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, _GWL_STYLE)
        exstyle = user32.GetWindowLongW(hwnd, _GWL_EXSTYLE)
        rect = _RECT(0, 0, int(client_w), int(client_h))
        user32.AdjustWindowRectEx(ctypes.byref(rect), style, False, exstyle)
        ow = rect.right - rect.left
        oh = rect.bottom - rect.top
        return max(ow, client_w), max(oh, client_h)
    except Exception:
        return client_w, client_h


# Reading-column layout in CSS logical pixels (#page is border-box).
_PAGE_CONTENT_LOGICAL = 860
_PAGE_HPAD_LOGICAL = 48
_PAGE_MAX_LOGICAL = _PAGE_CONTENT_LOGICAL + 2 * _PAGE_HPAD_LOGICAL  # 956
_SCROLLBAR_GUTTER_LOGICAL = 24
_READING_SIDE_MARGIN_LOGICAL = 64
_TARGET_READING_CLIENT_LOGICAL = (
    _PAGE_MAX_LOGICAL + _SCROLLBAR_GUTTER_LOGICAL + 2 * _READING_SIDE_MARGIN_LOGICAL
)  # 1108


def _hwnd_dpi_scale(hwnd) -> float:
    """Physical/logical scale for hwnd (1.0 at 96 DPI)."""
    if not hwnd:
        return 1.0
    try:
        dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
        return max(dpi / 96.0, 1.0)
    except Exception:
        return 1.0


def _outer_logical_for_client_logical(client_w: int, client_h: int, hwnd: int):
    """Return outer (frame) logical size for a target client logical area."""
    scale = _hwnd_dpi_scale(hwnd)
    phys_cw = int(round(client_w * scale))
    phys_ch = int(round(client_h * scale))
    phys_ow, phys_oh = _get_required_window_size_for_client(phys_cw, phys_ch, hwnd)
    return int(round(phys_ow / scale)), int(round(phys_oh / scale))


def _geometry_from_window(api) -> tuple | None:
    """Logical-pixel window rect for config save/restore (pywebview, not GetWindowRect)."""
    w = getattr(api, '_window', None)
    if not w:
        return None
    try:
        return int(w.x), int(w.y), int(w.width), int(w.height)
    except (AttributeError, TypeError, ValueError):
        return None


def _logical_work_area_for(hwnd):
    """Work area of the monitor containing hwnd, converted to logical pixels."""
    work = _work_area_for(hwnd)
    if not work:
        return None
    scale = _hwnd_dpi_scale(hwnd)
    wx, wy, ww, wh = work
    return (int(round(wx / scale)), int(round(wy / scale)),
            int(round(ww / scale)), int(round(wh / scale)))


def _enable_native_resize(hwnd):
    """Re-add WS_THICKFRAME so the OS handles resize at window edges natively.

    pywebview's frameless mode strips this style. Without it, DefWindowProc
    ignores resize hit-tests, so the window is effectively locked in size.

    Preserves the client-area screen origin when re-applying the frame so the
    window does not jump left on the first click after focus regain.
    """
    if not hwnd:
        return
    user32 = ctypes.windll.user32
    style = user32.GetWindowLongW(hwnd, _GWL_STYLE)
    exstyle = user32.GetWindowLongW(hwnd, _GWL_EXSTYLE)
    new_style = style | _WS_THICKFRAME
    if style == new_style:
        return
    user32.SetWindowLongW(hwnd, _GWL_STYLE, new_style)

    client_pt = _POINT()
    user32.ClientToScreen(hwnd, ctypes.byref(client_pt))
    cr = _RECT()
    user32.GetClientRect(hwnd, ctypes.byref(cr))
    client_w = cr.right - cr.left
    client_h = cr.bottom - cr.top
    rect = _RECT(0, 0, client_w, client_h)
    user32.AdjustWindowRectEx(ctypes.byref(rect), new_style, False, exstyle)
    outer_x = client_pt.x + rect.left
    outer_y = client_pt.y + rect.top
    outer_w = rect.right - rect.left
    outer_h = rect.bottom - rect.top
    # SWP_NOZORDER | NOACTIVATE | FRAMECHANGED — explicit pos/size keeps client fixed
    user32.SetWindowPos(hwnd, 0, outer_x, outer_y, outer_w, outer_h, 0x0004 | 0x0010 | 0x0020)
    _dlog('_enable_native_resize: WS_THICKFRAME applied hwnd=%s client=%sx%s outer=%sx%s',
          hwnd, client_w, client_h, outer_w, outer_h)
