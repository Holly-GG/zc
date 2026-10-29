import json,subprocess,sys,time,os
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/"test-results/stationery-x11";out.mkdir(parents=True,exist_ok=True)
settings=out/"settings.json";probe=out/"probe.json";counter=out/"clicks.txt"
settings.write_text(json.dumps(dict(position=[850,250],width=240,roaming=False,always_on_top=True)))
probe.unlink(missing_ok=True);counter.unlink(missing_ok=True);(out/"life.json").unlink(missing_ok=True)
env=os.environ.copy();env["QT_QPA_PLATFORM"]="xcb";xdot=os.environ.get("XDOTOOL_BIN","xdotool")
def x(*args):return subprocess.check_output([xdot,*map(str,args)],env=env,text=True).strip()
def state():
    for _ in range(20):
        try:return json.loads(probe.read_text())
        except (OSError,ValueError):time.sleep(.05)
    raise RuntimeError("probe")
def click(point,button=1):
    x("mousemove","--sync",*point);x("click",button);time.sleep(.25)
u=subprocess.Popen([sys.executable,str(root/"tools/test_x11.py"),"--underlay",str(counter)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
pet=None
try:
    time.sleep(.8);pet=subprocess.Popen([sys.executable,str(root/"main.py"),"--settings",str(settings),"--probe",str(probe)],env=env,stdout=(out/"pet.log").open("w"),stderr=subprocess.STDOUT)
    for _ in range(250):
        if probe.exists():break
        if pet.poll() is not None:raise RuntimeError("pet exited")
        time.sleep(.1)
    time.sleep(.3);s=state();point=(s["position"][0]+s["size"][0]//2,s["position"][1]+s["size"][1]*2//3)
    click(point,3);x("key",*(["Down"]*8),"Return")
    for _ in range(100):
        if state().get("dashboard"):break
        time.sleep(.1)
    dash=state()["dashboard"];assert dash
    click(dash["nav"]["3"]);dash=state()["dashboard"];source=dash["bag_cards"]["water_fountain"];rect=dash["rect"]
    target=next(pt for pt in [(1020,620),(1050,150),(20,660),(20,40)] if not(rect[0]<=pt[0]<=rect[0]+rect[2] and rect[1]<=pt[1]<=rect[1]+rect[3]))
    x("mousemove","--sync",*source);x("mousedown",1);time.sleep(.1);x("mousemove","--sync",source[0]+20,source[1]+20);time.sleep(.2);x("mousemove","--sync",*target);time.sleep(.2);x("mouseup",1);time.sleep(.5)
    assert state()["desktop_props"],(source,target,state())
    print("PASS actual backpack-card drag into desktop",flush=True)
    pos=state()["desktop_props"][0]["position"];count=int(counter.read_text());click((pos[0]+2,pos[1]+2));assert int(counter.read_text())==count+1
    print("PASS prop transparent corner passes actual click",flush=True)
    x("windowactivate","--sync",x("search","--name","年糕生活馆").splitlines()[0]);time.sleep(.2)
    click(state()["dashboard"]["clear"]);time.sleep(.4);assert not state()["desktop_props"]
    print("PASS actual one-click cleanup",flush=True)
finally:
    if pet and pet.poll() is None:pet.terminate();pet.wait(timeout=10)
    u.terminate();u.wait(timeout=10)
