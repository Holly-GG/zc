from datetime import date,timedelta,datetime,timezone
import json,random
import pytest
from niangao.life.calendar_cn import FIRST,LAST,lunar,lunar_label,china_now
from niangao.prop_physics import Body,accepts
from niangao.geometry import Rect

def test_calendar_every_date_in_50_years():
    day=FIRST;count=0
    while day<=LAST:
        assert lunar(day).toSolarDate()==day
        assert lunar_label(day)
        count+=1;day+=timedelta(days=1)
    assert count==18263
    assert lunar_label(date(2024,2,10))=='春节'
    assert lunar_label(date(2025,1,29))=='春节'
    assert lunar(date(2023,3,22)).isLeapMonth
    assert china_now(datetime(2026,10,28,18,tzinfo=timezone.utc).timestamp()).date()==date(2026,10,29)
    with pytest.raises(ValueError):lunar(date(2070,1,1))

def test_physics_platform_no_tunnelling_and_rate_independence():
    area=Rect(0,0,1200,900);platform=Rect(100,400,600,1)
    positions=[]
    for fps in (30,60,144):
        body=Body(200,50,0,900)
        for _ in range(fps*2):body.advance(1/fps,100,100,area,[platform])
        positions.append(body.y);assert body.grounded and body.y==300
    assert max(positions)-min(positions)<.1
    ball=Body(200,780)
    ball.advance(.25,100,100,area,bounce=True);assert ball.vy<0
    mouse=Body(1080,780,55,0);mouse.advance(.2,100,100,area,running=True);assert mouse.vx<0

def test_mood_changes_acceptance_without_forcing():
    high=dict(satiety=10,mood=95,energy=95);low=dict(satiety=100,mood=10,energy=5)
    for kind in ('consumable','toy'):
        a=random.Random(12);b=random.Random(12)
        assert sum(accepts(high,kind,a) for _ in range(1000))>sum(accepts(low,kind,b) for _ in range(1000))+400

def test_local_corpus_unique_contextual_and_no_recent_repeat():
    from niangao.dialogue import _CORPUS,choose,context_for
    assert len(_CORPUS)==len({r['text'] for r in _CORPUS})==1000
    assert len({r['context'] for r in _CORPUS})==40
    assert max(len(r['text']) for r in _CORPUS)<=42
    assert len({choose('water') for _ in range(9)})==9
    assert context_for('记得喝水')=='water'

@pytest.fixture(scope='module')
def pet(tmp_path_factory):
    from PySide6.QtWidgets import QApplication
    from niangao.pet import PetWindow
    from niangao.config import Settings
    app=QApplication.instance() or QApplication([])
    p=PetWindow(Settings(tmp_path_factory.mktemp('work')/'settings.json'));p.timer.stop();p.show()
    yield p
    p.close();app.processEvents()

def test_common_head_scale_and_stage(pet):
    art=pet.art;width=240;height=art.stage_height(width);scales=[]
    for state,frames in art.frames.items():
        for index,frame in enumerate(frames):
            rect=art.projection(state,index,width,height)
            assert rect.left()>=7 and rect.top()>=7 and rect.right()<=width-7 and rect.bottom()<=height-7
            scales.append(rect.width()/frame.width()*art.head_pixels[state][index])
    assert max(scales)-min(scales)<1e-8
    sizes=[]
    for action in ('idle','sleep','walk','roll','hang','feed'):
        pet.perform_action(action);sizes.append((pet.width(),pet.height()))
    assert len(set(sizes))==1

def test_static_work_mode_click_dialog_and_position_restore(pet):
    original=(pet.width(),pet.height());normal_pos=pet.pos();width=pet.settings.data['width']
    pet.set_work_mode(True);assert pet.size().width()==96 and not pet.work_icon.isNull()
    image=pet.pixmap.toImage();pet.tick();assert image==pet.pixmap.toImage()
    assert not pet.perform_action('pounce')
    pet.open_work();assert pet.work_panel.isVisible()
    pet.work_panel.text.setText('今天要认真工作');pet.work_panel.send();assert '年糕' in pet.work_panel.log.toPlainText()
    pet.move(120,140);pet.save();assert pet.settings.data['work_position']==[120,140]
    pet.set_work_mode(False);assert pet.settings.data['width']==width and (pet.width(),pet.height())==original
    assert pet.settings.data['position']==[normal_pos.x(),normal_pos.y()]

def test_food_packet_single_drop_cleanup_and_no_duplication(pet):
    from PySide6.QtCore import QPoint
    m=pet.desktop;m.clear();pet.life.data['inventory']['freeze_dried']=1;pet.life.data['freeze_packets']=[]
    assert m.place('freeze_dried',QPoint(300,200))[0]
    uid=next(iter(m.widgets));assert m.drop_piece(uid)
    assert m.widgets[uid].record['remaining']==7
    assert pet.life.data['inventory']['freeze_piece']==1
    m.clear();assert pet.life.data['freeze_packets']==[7]
    assert m.place('freeze_dried',QPoint(300,200))[0]
    uid=next(iter(m.widgets));assert m.widgets[uid].record['remaining']==7
    for _ in range(7):assert m.drop_piece(uid)
    assert uid not in m.widgets and pet.life.data['inventory']['freeze_dried']==0
    assert pet.life.data['inventory']['freeze_piece']==8
    m.clear();assert pet.life.data['freeze_packets']==[]

def test_focus_widget_keywords_and_true_elapsed_timer(pet):
    pet.open_focus();panel=pet.focus_panel
    panel.entry.setText('工作后喝水');panel.add();assert pet.life.data['tasks'][-1]['text']=='工作后喝水'
    panel.minutes.setValue(1);pet.life.focus_start(1);deadline=pet.life.focus_deadline
    pet.life.clock=lambda:deadline+1;pet.life.tick();assert pet.life.data['focus']['remaining']==0
    panel.refresh();assert panel.tasks.count()>=1;panel.close();assert not panel.isVisible()

def test_furniture_choreography_has_assets_and_can_be_interrupted(pet):
    from PySide6.QtCore import QPoint
    from niangao.furniture import FurnitureSession
    pet.desktop.clear();pet.life.data['inventory']['tree']=1
    assert pet.desktop.place('tree',QPoint(400,400))[0]
    widget=next(iter(pet.desktop.widgets.values()));widget.timer.stop()
    pet.furniture=FurnitureSession(pet,widget,random.Random(1))
    session=pet.furniture
    session.tick(session.started+3.1);assert pet.behaviour.state=='climb'
    session.tick(session.started+7.1);assert pet.behaviour.state=='climb_top'
    assert pet.geometry().top()>=pet.screen().availableGeometry().top()
    pet.pet_head();assert session.cancelled and pet.furniture is None
    pet.desktop.clear()


def test_network_time_rolls_over_without_another_api_request(tmp_path):
    from niangao.life.engine import LifeEngine
    from niangao.life.calendar_cn import CHINA
    clock=[100.]
    engine=LifeEngine(tmp_path/'time.json',clock=lambda:clock[0],wall=lambda:0)
    engine.data['preferences']['network_time']=True
    engine.calibrate_time(datetime(2026,10,29,23,59,50,tzinfo=CHINA))
    assert engine.today()==date(2026,10,29)
    clock[0]+=20
    assert engine.today()==date(2026,10,30)
    engine.data['preferences']['network_time']=False
    assert engine.today()==date(1970,1,1)
