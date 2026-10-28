import random
import pytest
from niangao.geometry import Rect,clamp_position,nearest_area,edge_barriers,hits_edge,bubble_position,physical_to_logical
from niangao.config import Settings
from niangao.behaviour import Behaviour

@pytest.mark.parametrize('area,expected',[(Rect(0,0,1920,1040),(1668,716)),(Rect(-1920,0,1920,1040),(-252,716))])
def test_bottom_right_uses_work_area(area,expected):
    assert clamp_position(99999,99999,240,312,area)==expected

def test_monitor_disconnect_clamps_saved_point():
    area=nearest_area(-1900,100,[Rect(0,0,1280,760)])
    assert clamp_position(-1900,100,240,312,area)==(12,100)

def test_negative_monitor_selected():
    a,b=Rect(-1920,0,1920,1040),Rect(0,0,1920,1040)
    assert nearest_area(-1600,300,[b,a])==a

@pytest.mark.parametrize('pet',[Rect(700,600,240,312),Rect(10,10,240,312),Rect(-1800,100,240,312)])
def test_dialogue_never_covers_pet(pet):
    area=Rect(-1920,0,3840,1040)
    pos=bubble_position(pet,244,82,area)
    assert pos is not None
    bubble=Rect(*pos,244,82)
    assert not pet.intersects(bubble) and area.contains(bubble)

def test_bubble_hides_if_no_space():
    assert bubble_position(Rect(0,0,240,312),244,82,Rect(0,0,240,312)) is None

def test_edges_block_entry_but_not_application_interior():
    app=Rect(300,200,400,400)
    assert hits_edge(Rect(100,250,100,100),Rect(210,250,100,100),[app])
    assert not hits_edge(Rect(330,240,100,100),Rect(400,280,100,100),[app])

def test_new_window_does_not_trap_pet_on_edge():
    app=Rect(300,200,400,400)
    assert not hits_edge(Rect(299,250,100,100),Rect(290,250,100,100),[app])

def test_mixed_dpi_coordinates():
    r=physical_to_logical(Rect(-2640,300,1200,900),(-2880,0),(-1920,0),1.5)
    assert r==Rect(-1760,200,800,600)

def test_config_round_trip(tmp_path):
    config=Settings(tmp_path/'settings.json')
    config.data['position']=[123,456];config.data['width']=280
    assert config.save()
    assert Settings(config.path).data==config.data

def test_invalid_config_is_recoverable(tmp_path):
    p=tmp_path/'settings.json';p.write_text('{bad')
    config=Settings(p)
    assert config.data['width']==240 and config.error
    p.write_text('{"width":"huge","position":["bad",9],"always_on_top":"yes"}')
    config=Settings(p)
    assert config.data['width']==240 and config.data['position'] is None and config.data['always_on_top'] is True

def test_state_timeout_uses_monotonic_clock():
    now=[100.0];b=Behaviour(random.Random(1),lambda:now[0]);b.action('pet',4)
    area=Rect(0,0,1280,760)
    assert b.tick(50,50,240,312,area,[],0.05)==(50,50)
    now[0]=105
    b.tick(50,50,240,312,area,[],0.05)
    assert b.state=='walk'

def test_sleep_cannot_move_until_woken():
    now=[100.0];b=Behaviour(clock=lambda:now[0]);b.action('sleep')
    now[0]=100000
    assert b.tick(50,50,240,312,Rect(0,0,1280,760),[],0.05)==(50,50)
    b.wake();assert b.state=='idle'

def test_walk_is_frame_rate_independent():
    def run(dt,count):
        b=Behaviour(clock=lambda:100);b.state='walk';b.target=(800,100);b.deadline=200
        x,y=100,100
        for _ in range(count):x,y=b.tick(x,y,100,100,Rect(0,0,1920,1040),[],dt)
        return x,y
    assert run(1/30,30)==pytest.approx(run(1/60,60))

def test_resume_does_not_teleport():
    b=Behaviour(clock=lambda:100);b.state='walk';b.target=(800,100);b.deadline=200
    x,y=b.tick(100,100,100,100,Rect(0,0,1920,1040),[],1000)
    assert x-100<=58*0.08+0.001

def test_pause_roaming_keeps_position():
    b=Behaviour(clock=lambda:100);b.state='walk';b.target=(800,100);b.deadline=200
    assert b.tick(100,100,100,100,Rect(0,0,1920,1040),[],0.03,False)==(100,100)
