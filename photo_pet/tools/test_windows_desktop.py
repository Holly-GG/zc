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
    s=state()
    if s.get("work_mode") and s.get("body_point"):return tuple(round(v*s.get("pet_dpi",1)) for v in s["body_point"])
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
    for _ in range(40):
        if state()['counts']['clicked']==before+1:break
        time.sleep(.1)
    check(count()==n and state()['counts']['clicked']==before+1,'cat click reaches pet without leaking to lower application; lower='+str((n,count()))+' state='+str(state())+' bounds='+str((r.left,r.top,r.right,r.bottom)))
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
    # Hold over the real alpha silhouette: new input path must fire without an extra pet on release.
    bx,by=body();u.SetCursorPos(bx,by);mouse(2);time.sleep(1.1)
    check(state()['state']=='nibble','real held left-button triggers nibble photo action')
    mouse(4);time.sleep(.15)
    n=count();r=bounds();click(r.left+3,r.top+3)
    check(count()==n+1,'transparent corner remains click-through during new action')
    close(pet);saved=json.loads(settings.read_text(encoding='utf-8'));check(saved['width']==s['size'][0],'normal exit saves configuration')
    probe.unlink()
    life_path=out/'life.json';life_data=json.loads(life_path.read_text(encoding='utf-8'))
    life_data['preferences']['input_link']=True
    life_path.write_text(json.dumps(life_data),encoding='utf-8')
    pet=launch();check(state()['position']==saved['position'],'restart restores position')
    # Explicitly enabled test profile: a held Shift generates activity, never text.
    u.keybd_event(0x10,0,0,0);time.sleep(.3);u.keybd_event(0x10,0,2,0)
    for _ in range(20):
        if state()['state'] in ('keyboard_paw','peek_screen','typing_nod'):break
        time.sleep(.1)
    check(state()['state'] in ('keyboard_paw','peek_screen','typing_nod'),'opt-in keyboard activity invokes photo response')
    close(pet)
    # Owned real desktop props: same OS-input method as the cat, independent underlay.
    life_data=json.loads(life_path.read_text(encoding='utf-8'));life_data['preferences']['input_link']=False
    life_data['desktop_items']=[dict(uid='native-water',item='water_fountain',x=350,y=350,width=112,water=100,pinned=True)]
    life_path.write_text(json.dumps(life_data),encoding='utf-8');probe.unlink();pet=launch();time.sleep(.3)
    def prop_handle():return u.FindWindowW(None,'年糕物件 · native-water')
    def prop_rect():
        r=w.RECT();check(bool(prop_handle()),'native fountain window exists');assert u.GetWindowRect(prop_handle(),ctypes.byref(r));return r
    pr=prop_rect();n=count();click(pr.left+2,pr.top+2)
    check(count()==n+1,'fountain transparent corner reaches independent lower app')
    n=count();click(pr.left+56,pr.top+75)
    data=json.loads(life_path.read_text(encoding='utf-8'))
    check(count()==n and data['desktop_items'][0]['water']==80,'fountain body click drinks and decreases stored water')
    bx,by=pr.left+56,pr.top+75;u.SetCursorPos(bx,by);mouse(2);time.sleep(.12);u.SetCursorPos(bx-45,by-30);time.sleep(.25);mouse(4);time.sleep(.3)
    data=json.loads(life_path.read_text(encoding='utf-8'));check(data['desktop_items'][0]['x']!=350,'native desktop prop left drag persists')
    # Open dashboard from its existing eighth selectable cat context-menu entry.
    click(*body(),button='right')
    for _ in range(8):key(0x28)
    key(0x0D)
    for _ in range(300):
        if state().get('dashboard'):break
        time.sleep(.1)
    dash=state().get('dashboard');check(bool(dash),'native menu opens compact dashboard')
    def ui_point(point,dashboard):return tuple(round(v*dashboard.get('dpi',1)) for v in point)
    click(*ui_point(dash['nav']['3'],dash));time.sleep(.3);dash=state()['dashboard']
    if dash.get('fullpage'):
        check(dash.get('page')=='backpack','original artwork sidebar hotspot opens the real backpack page')
        source=ui_point(dash['bag_cards']['fish'],dash);x,y,dw,dh=[v*dash.get('dpi',1) for v in dash['rect']]
        target=next(pt for pt in [(25,730),(u.GetSystemMetrics(0)-25,150),(25,80)] if not (x<=pt[0]<=x+dw and y<=pt[1]<=y+dh))
        u.SetCursorPos(*source);mouse(2);time.sleep(.12);u.SetCursorPos(source[0]+18,source[1]+18);time.sleep(.15);u.SetCursorPos(*target);time.sleep(.25);mouse(4);time.sleep(.4)
        check(any(v['item']=='fish' for v in state()['desktop_props']),'original artwork item image drags to a real desktop prop')
        click(*ui_point(dash['full_bag'],dash));time.sleep(.3);dash=state()['dashboard']
    # First clear the restored fountain using the actual dashboard button.
    click(*ui_point(dash['clear'],dash));time.sleep(.25)
    check(not state()['desktop_props'],'one-click clear removes own props without closing underlay')
    # The richer cards may put the fountain below the fold. Scroll with actual
    # Win32 wheel events instead of dragging a clipped/off-screen card position.
    for _ in range(30):
        dash=state()['dashboard']
        if 'water_fountain' in dash['bag_cards']:break
        vx,vy,vw,vh=dash['viewport'];u.SetCursorPos(*ui_point([vx+vw*.8,vy+vh*.65],dash));mouse(0x0800,-120);time.sleep(.15)
    check('water_fountain' in dash['bag_cards'],'backpack scrolling exposes a real visible product image')
    source=ui_point(dash['bag_cards']['water_fountain'],dash);x,y,dw,dh=[v*dash.get('dpi',1) for v in dash['rect']]
    candidates=[(25,730),(u.GetSystemMetrics(0)-25,150),(25,80),(u.GetSystemMetrics(0)-25,u.GetSystemMetrics(1)-160)]
    target=next(pt for pt in candidates if not (x<=pt[0]<=x+dw and y<=pt[1]<=y+dh))
    u.SetCursorPos(*source);mouse(2);time.sleep(.12);u.SetCursorPos(source[0]+18,source[1]+18);time.sleep(.15);u.SetCursorPos(*target);time.sleep(.25);mouse(4);time.sleep(.5)
    check(any(v['item']=='water_fountain' for v in state()['desktop_props']),'real backpack-image drag to desktop places fountain; source='+str(source)+' target='+str(target)+' drag='+str(state().get('card_drag'))+' props='+str(state().get('desktop_props'))+' dpi='+str(dash.get('dpi'))+' pet='+str(state().get('position'))+' size='+str(state().get('size')))
    for _ in range(30):
        dash=state()['dashboard']
        if dash['scroll']==0:break
        vx,vy,vw,vh=dash['viewport'];u.SetCursorPos(*ui_point([vx+vw*.8,vy+vh*.65],dash));mouse(0x0800,120);time.sleep(.15)
    check(dash['scroll']==0,'native wheel returns to the cleanup control')
    click(*ui_point(dash['clear'],dash));time.sleep(.25)
    data=json.loads(life_path.read_text(encoding='utf-8'))
    check(not state()['desktop_props'] and data['inventory']['water_fountain']==1,'cleanup returns placement to inventory without deleting owned stock')
    if dash.get('return_skin'):
        click(*ui_point(dash['return_skin'],dash));time.sleep(.3);dash=state()['dashboard']
        click(*ui_point(dash['nav']['5'],dash));time.sleep(.3);dash=state()['dashboard']
        check(dash.get('fullpage') and dash.get('page')=='chat','full-page chat hotspot opens original artwork with live input')
        click(*ui_point(dash['chat_input'],dash))
        for code in (0x53,0x4B,0x49,0x4E):key(code)
        key(0x0D);time.sleep(.5)
        import sqlite3
        with sqlite3.connect(str(out/'chat.sqlite3')) as db:
            check(db.execute("SELECT COUNT(*) FROM messages WHERE role='user' AND lower(content)='skin'").fetchone()[0]>=1,'full-page chat receives native typing and persists the actual message')
    close(pet)
    # New dynamic objects use actual moving coordinates; legacy mask/drag test above pins its fixture.
    life_data=json.loads(life_path.read_text(encoding='utf-8'))
    life_data['inventory'].update(ball=1,mouse=1)
    life_data['desktop_items']=[dict(uid='gravity-ball',item='ball',x=300,y=180,width=112,water=100),dict(uid='running-mouse',item='mouse',x=600,y=180,width=112,water=100)]
    life_path.write_text(json.dumps(life_data),encoding='utf-8');probe.unlink();pet=launch();time.sleep(1.4)
    dynamic={v['uid']:v for v in state()['desktop_props']}
    check(dynamic['gravity-ball']['position'][1]>180,'ball falls under real elapsed-time gravity')
    old_x=dynamic['running-mouse']['position'][0];time.sleep(.5)
    dynamic={v['uid']:v for v in state()['desktop_props']}
    check(abs(dynamic['running-mouse']['position'][0]-old_x)>5,'windup mouse runs on the real desktop')
    close(pet)
    saved=json.loads(settings.read_text(encoding='utf-8'));saved.update(work_mode=True,work_position=[650,250]);settings.write_text(json.dumps(saved),encoding='utf-8')
    probe.unlink();pet=launch();check(state()['work_mode'] and state()['size'][0]==160 and state()['work_pose'] in ('idle','bored','tail_sway','ear_flick','lick_paw','groom','yawn','expectant'),'work mode restores compact random idle poses')
    before=state()['position'];time.sleep(1);check(state()['position']==before,'work avatar does not roam without input')
    n=count();r=bounds();click(r.left+2,r.top+2);check(count()==n+1,'work avatar transparent corner passes real OS clicks')
    check(state()['work_panel_visible'] and state()['work_panel_inputs'],'work mode automatically shows its dialogue input and send button')
    panel_handle=u.FindWindowW(None,'年糕 · 桌面工作台');check(bool(panel_handle),'work dialogue has an accessible native window')
    u.PostMessageW(panel_handle,0x10,0,0);time.sleep(.3);check(not state()['work_panel_visible'],'close dialogue only hides the work panel')
    click(*body());check(state()['work_panel_visible'] and state()['work_panel_inputs'],'click idle avatar reopens dialogue and visible input')
    sent=state()["work_sent"]
    for code in (0x48,0x49):key(code)
    key(0x0D);time.sleep(.3)
    check(state()['work_panel_visible'] and state()['work_sent']==sent+1,'work input accepts native keyboard typing and Enter')
    import sqlite3
    with sqlite3.connect(str(out/'chat.sqlite3')) as db:
        check(db.execute("SELECT COUNT(*) FROM messages WHERE role='user' AND lower(content)='hi'").fetchone()[0]>=1,'native typed chat is saved in local SQLite')
    check(any((out/'chat_sessions').glob('*.json')),'per-session JSON archive files are created')
    close(pet)
    saved=json.loads(settings.read_text(encoding='utf-8'));saved['work_mode']=False;settings.write_text(json.dumps(saved),encoding='utf-8')
    life_data=json.loads(life_path.read_text(encoding='utf-8'));life_data['inventory'].update(food=1,litter=1)
    life_data['desktop_items']=[dict(uid='native-food',item='food',x=300,y=250,width=112,water=100,pinned=True,remaining=12),dict(uid='native-litter',item='litter',x=480,y=350,width=112,water=100,pinned=True,dirt=2)]
    life_path.write_text(json.dumps(life_data),encoding='utf-8');probe.unlink();pet=launch()
    food_handle=u.FindWindowW(None,'年糕物件 · native-food');r=w.RECT();assert u.GetWindowRect(food_handle,ctypes.byref(r))
    n=count();click(r.left+56,r.top+75,button='right')
    data=json.loads(life_path.read_text(encoding='utf-8'))
    check(count()==n and next(v for v in data['desktop_items'] if v['uid']=='native-food')['remaining']==11 and any(v['item']=='kibble_piece' for v in data['desktop_items']),'native right click drops exactly one grain without opening a menu')
    litter_handle=u.FindWindowW(None,'年糕物件 · native-litter');r=w.RECT();assert u.GetWindowRect(litter_handle,ctypes.byref(r))
    click(r.left+56,r.top+65,button='right');key(0x28);key(0x28);key(0x0D);time.sleep(.3)
    data=json.loads(life_path.read_text(encoding='utf-8'))
    check(next(v for v in data['desktop_items'] if v['uid']=='native-litter')['dirt']==0,'native litter context menu scoops stored dirty clumps')
    close(pet)
    print('WINDOWS_DESKTOP_RESULT passed; native Win32 mouse input and window bounds verified on this runner',flush=True)
except Exception as exc:
    print('::error::Windows desktop test failed: '+str(exc).replace('\n',' '),flush=True)
    traceback.print_exc();sys.exit(1)
finally:
    if pet and pet.poll() is None:
        try:close(pet)
        except Exception:pet.terminate();pet.wait(timeout=10)
    if under and under.poll() is None:under.terminate();under.wait(timeout=10)
