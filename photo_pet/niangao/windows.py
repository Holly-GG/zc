"""Window BOUNDS only. Never captures screens, reads app content or installs hooks."""
import os, sys
from .geometry import Rect, physical_to_logical

class WindowObstacles:
    def __init__(self):
        self.last_error=""
        self.supported=sys.platform=="win32"
        if not self.supported:return
        import ctypes
        from ctypes import wintypes as w
        self.c,self.w=ctypes,w
        self.user=ctypes.WinDLL("user32",use_last_error=True)
        self.dwm=ctypes.WinDLL("dwmapi",use_last_error=True)
        self.callback_type=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
        class MONITORINFOEX(ctypes.Structure):
            _fields_=[("cbSize",w.DWORD),("rcMonitor",w.RECT),("rcWork",w.RECT),("dwFlags",w.DWORD),("szDevice",w.WCHAR*32)]
        self.monitor_type=MONITORINFOEX
        u=self.user
        u.EnumWindows.argtypes=[self.callback_type,w.LPARAM];u.EnumWindows.restype=w.BOOL
        u.IsWindowVisible.argtypes=[w.HWND];u.IsWindowVisible.restype=w.BOOL
        u.IsIconic.argtypes=[w.HWND];u.IsIconic.restype=w.BOOL
        u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
        u.GetWindowRect.argtypes=[w.HWND,ctypes.POINTER(w.RECT)];u.GetWindowRect.restype=w.BOOL
        u.GetClassNameW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
        u.GetWindowLongPtrW.argtypes=[w.HWND,ctypes.c_int];u.GetWindowLongPtrW.restype=ctypes.c_ssize_t
        u.MonitorFromWindow.argtypes=[w.HWND,w.DWORD];u.MonitorFromWindow.restype=w.HANDLE
        u.GetMonitorInfoW.argtypes=[w.HANDLE,ctypes.POINTER(MONITORINFOEX)];u.GetMonitorInfoW.restype=w.BOOL
        self.dwm.DwmGetWindowAttribute.argtypes=[w.HWND,w.DWORD,w.LPVOID,w.DWORD]

    def query(self, screens):
        if not self.supported:return []
        c,w,u=self.c,self.w,self.user
        found=[]
        def visit(hwnd,_param):
            try:
                pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,c.byref(pid))
                if pid.value==os.getpid() or not u.IsWindowVisible(hwnd) or u.IsIconic(hwnd):return True
                if u.GetWindowLongPtrW(hwnd,-20)&0x80:return True # tool windows
                klass=c.create_unicode_buffer(128);u.GetClassNameW(hwnd,klass,128)
                if klass.value in {"Progman","WorkerW","Shell_TrayWnd","Shell_SecondaryTrayWnd"}:return True
                cloaked=w.DWORD()
                if self.dwm.DwmGetWindowAttribute(hwnd,14,c.byref(cloaked),c.sizeof(cloaked))==0 and cloaked.value:return True
                r=w.RECT()
                # DWM frame bounds exclude invisible resize shadows.
                if self.dwm.DwmGetWindowAttribute(hwnd,9,c.byref(r),c.sizeof(r))!=0:
                    if not u.GetWindowRect(hwnd,c.byref(r)):return True
                if r.right-r.left<90 or r.bottom-r.top<60:return True
                info=self.monitor_type();info.cbSize=c.sizeof(info)
                u.GetMonitorInfoW(u.MonitorFromWindow(hwnd,2),c.byref(info))
                match=next((s for s in screens if s["name"].rsplit("\\",1)[-1].lower()==info.szDevice.rsplit("\\",1)[-1].lower()),screens[0])
                frame=physical_to_logical(Rect(r.left,r.top,r.right-r.left,r.bottom-r.top),
                    (info.rcMonitor.left,info.rcMonitor.top),match["origin"],match["scale"])
                found.append(frame)
            except Exception as exc:self.last_error=str(exc)
            return True
        callback=self.callback_type(visit)
        if not u.EnumWindows(callback,0):self.last_error="EnumWindows failed"
        return found
