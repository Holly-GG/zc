#!/usr/bin/env python3
"""Requires running X11 compositor, Godot, xdotool; uses isolated user data.
Example: xvfb-run -s '-screen 0 1280x800x24' python3 tools/test-desktop-x11.py
Start a compositor such as xcompmgr in that display before testing transparency.
"""
import os, subprocess, time, json, pathlib, argparse
parser=argparse.ArgumentParser()
parser.add_argument('--output', default='exports/test-results/x11')
args=parser.parse_args()
root=pathlib.Path(__file__).resolve().parent.parent
base=(root/args.output).resolve();base.mkdir(parents=True,exist_ok=True)
for folder in ['data','config','cache']:(base/'xdg'/folder).mkdir(parents=True,exist_ok=True)
user=base/'xdg/data/godot/app_userdata/Niangao P0'
env=os.environ.copy();env.update(XDG_DATA_HOME=str(base/'xdg/data'),XDG_CONFIG_HOME=str(base/'xdg/config'),XDG_CACHE_HOME=str(base/'xdg/cache'),LIBGL_ALWAYS_SOFTWARE='1')
xdot=os.environ.get('XDOTOOL_BIN', 'xdotool')
def x(*args): return subprocess.check_output([xdot,*map(str,args)],env=env,text=True).strip()
def latest(): return json.loads((user/'diagnostics.jsonl').read_text().splitlines()[-1])
def count(): return int((user/'underlay-count.txt').read_text())
def click(px,py): x('mousemove','--sync',px,py);time.sleep(.15);x('click','1');time.sleep(.4)
under=subprocess.Popen([os.environ.get('GODOT_BIN','godot'),'--path',str(root),'--audio-driver','Dummy','res://tests/input_probe.tscn'],env=env,stdout=(base/'underlay.log').open('w'),stderr=subprocess.STDOUT)
pet=None
try:
 time.sleep(2)
 pet=subprocess.Popen([os.environ.get('GODOT_BIN','godot'),'--path',str(root),'--audio-driver','Dummy','--','--diagnostics'],env=env,stdout=(base/'desktop.log').open('w'),stderr=subprocess.STDOUT)
 time.sleep(3)
 # Hide debug fallback; no system tray exists on virtual desktop.
 for wid in x('search','--name','Niangao P0.*DEBUG.*PLACEHOLDER').splitlines(): x('windowunmap',wid)
 wid=x('search','--name','^Niangao P0 PLACEHOLDER').splitlines()[-1]
 # Move into underlay area using the WM so clicks have a genuine second app below.
 x('windowmove',wid,650,250);time.sleep(2)
 state=latest();px,py=state['position'];sx,sy=state['size'];print('initial',state)
 before=count();click(px+10,py+10)
 assert count()==before+1, ('transparent click not delivered',before,count())
 print('PASS transparent corner delivered to underlay')
 before=count();before_pet=latest()['events'].get('PET_CLICKED',0);click(px+180,py+200)
 assert count()==before, 'opaque click leaked to underlay'
 assert latest()['events'].get('PET_CLICKED',0)==before_pet+1, latest()
 print('PASS opaque character clicked; underlay unchanged')
 # A concavity beside the head remains transparent within the cat bounding box.
 before=count();click(px+85,py+85)
 assert count()==before+1, 'silhouette concavity did not pass through'
 print('PASS transparent silhouette concavity delivered')
 old=latest()['position'];x('mousemove',px+180,py+200);x('mousedown','1');time.sleep(.2);x('mousemove','--sync',px+100,py+150);time.sleep(.4);x('mouseup','1');time.sleep(1)
 new=latest()['position'];assert new!=old,(old,new)
 print('PASS drag',old,'->',new)
 x('key','Escape');pet.wait(timeout=10);assert pet.returncode==0
 cfg=json.loads((user/'config.json').read_text());assert cfg['window']['position']==new,cfg
 print('PASS graceful exit and position persisted')
 pet=subprocess.Popen([os.environ.get('GODOT_BIN','godot'),'--path',str(root),'--audio-driver','Dummy','--','--diagnostics'],env=env,stdout=(base/'restart.log').open('w'),stderr=subprocess.STDOUT);time.sleep(3)
 assert latest()['position']==new,latest()
 print('PASS saved position restored on restart')
 print('DESKTOP_RESULT passed=7 failed=0 (Linux X11 only)')
finally:
 if pet and pet.poll() is None: pet.terminate();pet.wait(timeout=10)
 under.terminate();under.wait(timeout=10)
