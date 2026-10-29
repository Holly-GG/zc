"""Keep the active control window usable above our own topmost pet, Windows only."""
import sys
def present_window(widget):
    """Recover hidden/minimized/off-screen windows from every application entry."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    if widget.windowState() & Qt.WindowState.WindowMinimized:
        widget.setWindowState(widget.windowState() & ~Qt.WindowState.WindowMinimized)
    screens=QApplication.screens()
    if screens:
        area=(widget.screen() or screens[0]).availableGeometry()
        widget.resize(min(widget.width(),area.width()),min(widget.height(),area.height()))
        widget.move(max(area.left(),min(widget.x(),area.right()-widget.width()+1)),
                    max(area.top(),min(widget.y(),area.bottom()-widget.height()+1)))
    widget.show();widget.raise_();widget.activateWindow()

def prioritize_dashboard(widget,active):
    if sys.platform!="win32":return False
    import ctypes
    from ctypes import wintypes as w
    api=ctypes.WinDLL("user32",use_last_error=True)
    api.SetWindowPos.argtypes=[w.HWND,w.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,w.UINT]
    api.SetWindowPos.restype=w.BOOL
    # NOACTIVATE avoids focus recursion; NOTOPMOST on deactivation restores ordinary app stacking.
    try:return bool(api.SetWindowPos(w.HWND(int(widget.winId())),w.HWND(-1 if active else -2),0,0,0,0,0x0001|0x0002|0x0010))
    except (OSError,RuntimeError):return False
