# Frameless window, no native title bar/chrome

mdviewer runs frameless (`frameless=True` in pywebview) with a custom compact
title bar (theme/preset switcher, snap buttons, version badge) instead of the
OS-native window frame, for a minimal reading-tool aesthetic rather than a
generic app window.

**Consequence:** losing the native frame means resize, drag-to-move, and
window snapping no longer work for free — pywebview's frameless mode strips
`WS_THICKFRAME`, so `mdviewer.py` re-applies it via Win32 (`_enable_native_resize`)
after load and after every fullscreen toggle, and implements its own
`snap()` (left/right/reading) against `GetWindowRect`/`GetMonitorInfo`
instead of relying on OS window management.
