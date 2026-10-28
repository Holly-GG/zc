"""Optional key-activity boolean; no key names/text, hooks, clipboard or logging."""
import sys,time
class KeyboardActivity:
    def __init__(self,reader=None,clock=None):
        self.reader=reader;self.clock=clock or time.monotonic;self.last_poll=0;self.down=False;self.error=""
        if reader is None and sys.platform=="win32":
            import ctypes
            api=ctypes.WinDLL("user32")
            api.GetAsyncKeyState.argtypes=[ctypes.c_int];api.GetAsyncKeyState.restype=ctypes.c_short
            self.reader=lambda:any(api.GetAsyncKeyState(v)&0x8000 for v in range(8,223))
    @property
    def supported(self):return self.reader is not None
    def poll(self,enabled=False):
        if not enabled:self.down=False;return False
        now=self.clock()
        if self.reader is None or now-self.last_poll<.1:return False
        self.last_poll=now
        try:down=bool(self.reader())
        except Exception:self.error="键盘活动查询不可用";return False
        result=down and not self.down;self.down=down;return result
