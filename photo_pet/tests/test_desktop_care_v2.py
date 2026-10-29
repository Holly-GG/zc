import random
import pytest
from niangao.interaction.work_idle import WorkIdle

def test_quiet_work_scheduler_varies_poses_without_movement_actions():
    clock=[0.];idle=WorkIdle(random.Random(3),lambda:clock[0]);idle.reset();seen=set()
    counts={key:4 for key in idle.POSES};counts['idle']=1
    for _ in range(200):
        pose,index=idle.sample(counts);seen.add(pose);assert pose in idle.POSES and 0<=index<counts[pose]
        clock[0]+=2
    assert len(seen)>4 and 'walk' not in seen and 'pounce' not in seen
    clock[0]+=3600;pose,index=idle.sample(counts);assert pose in idle.POSES

@pytest.fixture(scope='module')
def pet(tmp_path_factory):
    from PySide6.QtWidgets import QApplication
    from niangao.pet import PetWindow
    from niangao.config import Settings
    app=QApplication.instance() or QApplication([]);p=PetWindow(Settings(tmp_path_factory.mktemp('care-v2')/'settings.json'));p.timer.stop();p.show()
    yield p
    p.close();app.processEvents()

def prop(pet,id):
    from PySide6.QtCore import QPoint
    pet.desktop.clear();pet.life.data['inventory'][id]=1
    assert pet.desktop.place(id,QPoint(400,300))[0]
    w=next(iter(pet.desktop.widgets.values()));w.timer.stop();w.pinned=True;w.record['pinned']=True
    return w

def test_food_interruption_is_free_and_finished_bite_consumes_once(pet):
    w=prop(pet,'fish');m=pet.desktop
    assert m.start_routine(w,'food');session=pet.furniture
    session.tick(session.started+session.approach+2);assert pet.life.data['inventory']['fish']==1
    session.cancel();assert w.uid in m.widgets
    assert m.start_routine(w,'food');session=pet.furniture
    session.tick(session.started+session.approach+4.1)
    assert session.committed and pet.life.data['inventory']['fish']==0 and w.uid not in m.widgets
    session.tick(session.started+session.total+1);assert pet.life.data['inventory']['fish']==0

def test_litter_use_dirt_clean_and_restart_persistence(pet):
    from niangao.life.engine import LifeEngine
    w=prop(pet,'litter');m=pet.desktop
    for count in range(1,4):
        assert m.start_routine(w,'litter');session=pet.furniture;session.tick(session.started+session.total+1)
        assert w.record['dirt']==count
    assert not m.start_routine(w,'litter')
    m.save();e=LifeEngine(pet.life.path);assert e.data['desktop_items'][0]['dirt']==3
    assert m.clean_litter(w.uid) and w.record['dirt']==0
    before=pet.life.data['stats']['cleanliness'];m.clean_litter(w.uid);assert pet.life.data['stats']['cleanliness']==before
    assert m.start_routine(w,'litter');pet.furniture.cancel();assert w.record['dirt']==0

def test_kibble_packet_right_click_single_grain_and_partial_return(pet):
    from PySide6.QtCore import Qt,QPoint
    from PySide6.QtTest import QTest
    w=prop(pet,'food');m=pet.desktop;pet.life.data['food_packets']['food']=[];pet.life.data['inventory']['kibble_piece']=0
    QTest.mouseClick(w,Qt.MouseButton.RightButton,pos=QPoint(w.width()//2,w.height()//2))
    assert w.record['remaining']==11 and pet.life.data['inventory']['kibble_piece']==1
    m.clear();assert pet.life.data['food_packets']['food']==[11]
    assert m.place('food',QPoint(400,300))[0]
    w=next(iter(m.widgets.values()));assert w.record['remaining']==11
    for _ in range(11):assert m.drop_piece(w.uid)
    assert pet.life.data['inventory']['food']==0 and pet.life.data['inventory']['kibble_piece']==12
    m.clear();assert not pet.life.data['food_packets']['food']

def test_bowl_portions_and_interruption_do_not_spend_food(pet):
    w=prop(pet,'food_bowl');m=pet.desktop
    pet.life.cooldowns['meal']=-1e12
    assert m.start_routine(w,'food');s=pet.furniture;s.cancel();assert w.record.get('servings',3)==3
    assert m.start_routine(w,'food');s=pet.furniture;s.tick(s.started+s.total+1)
    assert w.record['servings']==2
    from niangao.life.item_art import item_pixmap
    assert item_pixmap("food_bowl",96,True).toImage()!=item_pixmap("food_bowl",96,False).toImage()
    m.refill_food(w.uid);assert w.record['servings']==3

def test_small_food_settles_after_short_impact_bounces():
    from niangao.prop_physics import Body
    from niangao.geometry import Rect
    body=Body(200,100,80,-90)
    for _ in range(300):body.advance(1/60,38,38,Rect(0,0,1000,800),settle_bounce=True)
    assert body.grounded and body.vy==0 and abs(body.vx)<1
