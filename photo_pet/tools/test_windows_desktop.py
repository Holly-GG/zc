"""Interactive Win32 integration: real OS input, independent lower application.
Requires Windows and PySide6 in the test environment; tests the packaged exe.
Does not read screen pixels, window titles of other applications or app content.
"""
import argparse,ctypes,json,os,subprocess,sys,time,traceback
from ctypes import wintypes as w
from pathlib import Path

parser=argparse.ArgumentParser();parser.add_argument('--exe',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
u=ctypes.WinDLL('user32',use_last_error=True)
try:u.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except (AttributeError,OSError):pass
u.FindWindowW.argtypes=[w.LPCWSTR,w.LPCWSTR];u.FindWindowW.restype=w.HWND
u.GetWindowRect.argtypes=[w.HWND,ctypes.POINTER(w.RECT)];u.GetWindowRect.restype=w.BOOL
u.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int];u.SetCursorPos.restype=w.BOOL
u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];u.PostMessageW.restype=w.BOOL
u.mouse_event.argtypes=[w.DWORD,w.DWORD,w.DWORD,w.DWORD,ctypes.c_size_t]
settings=out/'settings.json';probe=out/'probe.json';counter=out/'clicks.txt'
settings.write_text(json.dumps({'position':[650,250],'width':240,'roaming':False,'always_on_top':True}))
probe.unlink(missing_ok=True);counter.unlink(missing_ok=True)
env=os.environ.copy();env['QT_QPA_PLATFORM']='windows'
def state():
    for _ in range(20):
        try:return json.loads(probe.read_text(encoding='utf-8'))
        except (ValueError,FileNotFoundError):time.sleep(.1)
    raise RuntimeError('No current pet state')
def count():return int(counter.read_text())
def handle():
    value=u.FindWindowW(None,'年糕 · 照片桌宠')
    if not value:raise RuntimeError('Pet native window not found')
    return value
def bounds():
    r=w.RECT();assert u.GetWindowRect(handle(),ctypes.byref(r))
    return r

def body():
    r=bounds();return r.left+(r.right-r.left)//2,r.top+(r.bottom-r.top)*2//3

def mouse(flags,data=0):u.mouse_event(flags,0,0,data,0)
def click(x,y,button='left'):
    assert u.SetCursorPos(round(x),round(y));time.sleep(.12)
    down,up=(2,4) if button=='left' else (8,16)
    mouse(down);time.sleep(.05);mouse(up);time.sleep(.35)
def key(code):
    u.keybd_event(code,0,0,0);time.sleep(.05);u.keybd_event(code,0,2,0)
def launch():
    p=subprocess.Popen([str(args.exe.resolve()),'--settings',str(settings),'--probe',str(probe)],env=env,stdout=(out/'pet.log').open('a'),stderr=subprocess.STDOUT)
    for _ in range(400):
        if p.poll() is not None:raise RuntimeError('Pet exited before probe: '+str(p.returncode))
        if probe.exists():return p
        time.sleep(.1)
    raise TimeoutError('Pet startup exceeded 40 seconds')
def close(p):
    u.PostMessageW(handle(),0x10,0,0);p.wait(timeout=10)
    assert p.returncode==0,('Exit code',p.returncode)
def check(condition,description):
    if not condition:raise AssertionError(description)
    print('PASS '+description,flush=True)
under=None;pet=None
try:
    under=subprocess.Popen([sys.executable,str(Path(__file__).with_name('test_x11.py')),'--underlay',str(counter)],env=env,stdout=(out/'underlay.log').open('w'),stderr=subprocess.STDOUT)
    for _ in range(200):
        if under.poll() is not None:raise RuntimeError('Underlay failed to start')
        if counter.exists():break
        time.sleep(.1)
    pet=launch();time.sleep(.6)
    s=state();check(s['native_obstacles'] and s['obstacles']>=1 and not s['provider_error'],'native EnumWindows detects independent window bounds')
    n=count();r=bounds();click(r.left+3,r.top+3)
    check(count()==n+1,'transparent corner click reaches lower application')
    n=count();before=state()['counts']['clicked'];click(*body())
    check(count()==n and state()['counts']['clicked']==before+1,'cat click reaches pet without leaking to lower application')
    # The visible head is narrower than the overall silhouette.
    n=count();r=bounds();click(r.left+8,r.top+22)
    check(count()==n+1,'transparent point within pet bounding rectangle reaches lower application')
    old=state()['position'];bx,by=body();u.SetCursorPos(bx,by);mouse(2);time.sleep(.15);u.SetCursorPos(bx-70,by-40);time.sleep(.35);mouse(4);time.sleep(.4)
    check(state()['position']!=old and state()['counts']['dragged']==1,'left-button drag changes position')
    old=state()['size'][0];u.SetCursorPos(*body());mouse(0x0800,120);time.sleep(.5)
    check(state()['size'][0]>old,'mouse wheel resizes pet')
    old=state()['counts']['head_pet'];click(*body(),button='right');key(0x28);key(0x0D);time.sleep(.4)
    check(state()['counts']['head_pet']==old+1,'native right-click menu invokes head pet')
    s=state()
    if s['bubble_visible']:
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent));from niangao.geometry import Rect
        check(not Rect(*s['position'],*s['size']).intersects(Rect(*s['bubble'])),'dialogue bubble avoids character')
    close(pet);saved=json.loads(settings.read_text(encoding='utf-8'));check(saved['width']==s['size'][0],'normal exit saves configuration')
    probe.unlink();pet=launch();check(state()['position']==saved['position'],'restart restores position');close(pet)
    print('WINDOWS_DESKTOP_RESULT passed; native Win32 mouse input and window bounds verified on this runner',flush=True)
except Exception as exc:
    print('::error::Windows desktop test failed: '+str(exc).replace('\n',' '),flush=True)
    traceback.print_exc();sys.exit(1)
finally:
    if pet and pet.poll() is None:
        try:close(pet)
        except Exception:pet.terminate();pet.wait(timeout=10)
    if under and under.poll() is None:under.terminate();under.wait(timeout=10)
