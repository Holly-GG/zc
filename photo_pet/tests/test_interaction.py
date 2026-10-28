import os,random,wave,struct
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt,QPoint
from PySide6.QtTest import QTest
from niangao.interaction.actions import ACTIONS,ROWS,SOUNDS,MOOD_POOLS
from niangao.interaction.director import Director
from niangao.interaction.input_link import KeyboardActivity
from niangao.interaction.audio import SoundPlayer,synthesize
def test_sequence_real_time_and_interrupt():
    clock=[100.];played=[];d=Director(lambda:clock[0],random.Random(1));play=lambda key,t:played.append((key,t)) or True
    d.feed(play);assert played[-1][0]=="feed";clock[0]+=3.1;d.tick(play);assert played[-1][0]=="mouth_lick"
    d.poke(play);interrupted=len(played);clock[0]+=20;d.tick(play);assert len(played)==interrupted+1 and played[-1][0]=="ear_flick"
    clock[0]+=30;d.tick(play);assert not d.active and all(v[0]!="leg_rub" for v in played)
def test_pause_and_unavailable_sequence():
    now=[10];d=Director(lambda:now[0]);played=[]
    d.sequence([("stalk",2),("pounce",2)],lambda k,t:played.append(k) or True);now[0]=20
    d.tick(lambda k,t:played.append(k) or True,True);assert played==["stalk"]
    d.tick(lambda k,t:played.append(k) or True);assert played==["stalk","pounce"]
    d.sequence([("made-up",1),("knead",1)],lambda k,t:False);assert not d.active
def test_emotions_have_valid_resources_and_explicit_shared_variants():
    assert set(["害羞","委屈","生气","犯困","兴奋","无聊","期待"])<=set(MOOD_POOLS)
    for pool in MOOD_POOLS.values():assert all(k in ACTIONS for k in pool)
    for key,info in ACTIONS.items():
        if key!=info.resource:assert info.note
def test_keyboard_optin_no_queries_when_disabled():
    calls=[];now=[2.];state=[True];reader=lambda:calls.append(True) or state[0];k=KeyboardActivity(reader,lambda:now[0])
    assert not k.poll(False) and not calls
    assert k.poll(True);now[0]+=.2;assert not k.poll(True)
    state[0]=False;now[0]+=.2;assert not k.poll(True)
    state[0]=True;now[0]+=.2;assert k.poll(True)
    count=len(calls);now[0]+=10;assert not k.poll(False) and len(calls)==count
def test_all_nine_sounds_pcm_and_off_by_default(tmp_path):
    for kind in SOUNDS:
        raw=synthesize(kind,50);assert len(raw)>10000 and len(raw)%2==0 and max(abs(v[0]) for v in struct.iter_unpack("<h",raw))>100
        assert set(synthesize(kind,0))=={0}
    events=[];prefs=dict(sound=False,volume=30);s=SoundPlayer(tmp_path,prefs,clock=lambda:10,backend=lambda p:events.append(p))
    assert not s.play("purr") and not events and not list(tmp_path.iterdir())
    prefs["sound"]=True;assert s.play("purr");assert not s.play("bell")
    with wave.open(str(events[0])) as f:assert f.getnchannels()==1 and f.getsampwidth()==2 and f.getframerate()==22050
    s.stop();assert events[-1] is None
def test_all_new_photo_actions_and_hold_poke_drag(tmp_path):
    from niangao.pet import PetWindow
    from niangao.config import Settings
    app=QApplication.instance() or QApplication([]);p=PetWindow(Settings(tmp_path/"settings.json"));p.show();app.processEvents()
    assert sum(len(keys) for keys in ROWS.values())==32
    for keys in ROWS.values():
        for key in keys:
            assert p.art.ensure(key)==key
            assert len(p.art.frames[key])==4 and len({bytes(f.constBits()) for f in p.art.frames[key]})==4
            assert p.perform_action(key)
            pix,mask=p.art.render(key,1,240,280);assert not mask.isNull()
    p.perform_action("idle");old=p.counts["head_pet"]
    QTest.mousePress(p,Qt.MouseButton.LeftButton,pos=QPoint(p.width()//2,p.height()//2));QTest.qWait(950)
    assert p.behaviour.state=="nibble"
    QTest.mouseRelease(p,Qt.MouseButton.LeftButton,pos=QPoint(100,100));assert p.counts["head_pet"]==old
    p.poke();assert p.behaviour.state in {"startle_jump","angry_shake","ignore","puff"}
    p.perform_action("sleep");p.motion_interactions(100000,.03);assert p.behaviour.state=="sleep"
    p.close();app.processEvents()
