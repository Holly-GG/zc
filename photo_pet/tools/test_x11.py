"""Real OS-input integration. Requires an X11 display, compositor and xdotool."""
import argparse,json,os,subprocess,sys,tempfile,time
from pathlib import Path

if '--underlay' in sys.argv:
    from PySide6.QtWidgets import QApplication,QWidget
    from PySide6.QtCore import Qt
    class Underlay(QWidget):
        def __init__(self,path):
            super().__init__(None,Qt.WindowType.FramelessWindowHint);self.path=Path(path);self.count=0
            self.setWindowTitle('Niangao Photo Underlay');self.setGeometry(0,0,1100,700)
            self.setStyleSheet('background:#8CCCCA;');self.write()
        def write(self):self.path.write_text(str(self.count))
        def mousePressEvent(self,event):
            if event.button()==Qt.MouseButton.LeftButton:self.count+=1;self.write()
    app=QApplication([]);w=Underlay(sys.argv[-1]);w.show();sys.exit(app.exec())

parser=argparse.ArgumentParser();parser.add_argument('--output',default='test-results/x11');args=parser.parse_args()
root=Path(__file__).resolve().parent.parent
out=(root/args.output).resolve();out.mkdir(parents=True,exist_ok=True)
settings=out/'settings.json';probe=out/'probe.json';count_path=out/'clicks.txt'
probe.unlink(missing_ok=True);count_path.unlink(missing_ok=True)
settings.write_text(json.dumps({'position':[650,250],'width':240,'roaming':False,'always_on_top':True}))
env=os.environ.copy();env['QT_QPA_PLATFORM']='xcb'
xdot=os.environ.get('XDOTOOL_BIN','xdotool')
def x(*a):return subprocess.check_output([xdot,*map(str,a)],env=env,text=True).strip()
def state():
    for _ in range(10):
        try:return json.loads(probe.read_text())
        except (ValueError,FileNotFoundError):time.sleep(.1)
    raise RuntimeError('No current pet state')
def click(px,py,button=1):x('mousemove','--sync',px,py);time.sleep(.1);x('click',button);time.sleep(.35)
def under_count():return int(count_path.read_text())
def body(s):return s['position'][0]+s['size'][0]//2,s['position'][1]+s['size'][1]*2//3
under=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--underlay',str(count_path)],env=env,stdout=(out/'underlay.log').open('w'),stderr=subprocess.STDOUT)
pet=None
try:
    time.sleep(1)
    pet=subprocess.Popen([sys.executable,str(root/'main.py'),'--settings',str(settings),'--probe',str(probe)],env=env,stdout=(out/'pet.log').open('w'),stderr=subprocess.STDOUT)
    for _ in range(100):
        if pet.poll() is not None:raise RuntimeError((out/'pet.log').read_text())
        if probe.exists():break
        time.sleep(.1)
    time.sleep(.3);s=state();px,py=s['position']
    n=under_count();click(px+3,py+3);assert under_count()==n+1
    print('PASS transparent corner reaches independent lower app',flush=True)
    n=under_count();cp=s['counts']['clicked'];click(*body(s));s=state()
    assert under_count()==n and s['counts']['clicked']==cp+1
    print('PASS cat receives click without leaking to lower app',flush=True)
    ox,oy=s['position'];bx,by=body(s)
    x('mousemove',bx,by);x('mousedown',1);time.sleep(.1);x('mousemove','--sync',bx-80,by-50);time.sleep(.3);x('mouseup',1);time.sleep(.3)
    s=state();assert s['position']!=[ox,oy] and s['counts']['dragged']==1
    print('PASS left-button drag',flush=True)
    before=s['size'][0];click(*body(s),button=4);s=state();assert s['size'][0]>before
    print('PASS wheel resize',flush=True)
    before=s['counts']['head_pet'];click(*body(s),button=3);x('key','Down','Return');time.sleep(.4)
    s=state();assert s['counts']['head_pet']==before+1
    print('PASS native right-click menu action',flush=True)
    if s['bubble_visible']:
        from_rect=__import__('sys').path
        sys.path.insert(0,str(root))
        from niangao.geometry import Rect
        assert not Rect(*s['position'],*s['size']).intersects(Rect(*s['bubble']))
    print('PASS dialogue does not overlap cat',flush=True)
    # Native menu exit: 7th selectable item (disabled title and separators skipped).
    click(*body(s),button=3);x('key',*(['Down']*7),'Return');pet.wait(timeout=8)
    assert pet.returncode==0
    saved=json.loads(settings.read_text());assert saved['width']==s['size'][0]
    print('PASS menu exit and config persistence',flush=True)
    probe.unlink()
    pet=subprocess.Popen([sys.executable,str(root/'main.py'),'--settings',str(settings),'--probe',str(probe)],env=env,stdout=(out/'restart.log').open('w'),stderr=subprocess.STDOUT)
    for _ in range(100):
        if probe.exists():break
        time.sleep(.1)
    assert state()['position']==saved['position']
    print('PASS saved position restored',flush=True)
    print('PHOTO_X11_RESULT passed=8 failed=0',flush=True)
finally:
    if pet and pet.poll() is None:pet.terminate();pet.wait(timeout=10)
    under.terminate();under.wait(timeout=10)
