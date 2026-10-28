import os,json,threading
from datetime import date
from http.server import HTTPServer,BaseHTTPRequestHandler
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint,Qt
from PySide6.QtTest import QTest
from niangao.life.engine import LifeEngine
from niangao.life.ai import AIClient,SecretVault
from niangao.life.catalog import BY_ID
from niangao.interaction.autonomy import AutonomyPolicy
from niangao.interaction.director import Director
from niangao.life.item_art import item_pixmap
def test_unattended_frequency_exactly_thirty_percent():
    now=[100.];p=AutonomyPolicy(lambda:now[0]);assert p.rate==.3 and p.interval(12)==40
    p.click();assert p.interval(12)==12;now[0]+=20;assert p.rate==.3 and p.interval(9)==30
    d=Director(lambda:now[0]);d.set_rate(.3);assert d.next_auto-now[0]==pytest.approx(40)
    now[0]+=10;d.set_rate(1);assert d.next_auto-now[0]==pytest.approx(9)
def test_profile_roundtrip_real_age_and_starter_once(tmp_path):
    path=tmp_path/"life.json";e=LifeEngine(path)
    e.data["profile"].update(personality="有点傲娇，熟悉后爱撒娇",habits="早晨爱喝水",likes="鱼",dislikes="噪声")
    e.data["age_override"]=6;e.save();copy=LifeEngine(path)
    assert copy.profile_snapshot()["identity"]["habits"]=="早晨爱喝水"
    assert copy.profile_snapshot()["virtual_age_months"]==6
    assert copy.profile_snapshot()["real_age"]==copy.age()["text"]
    assert copy.profile_snapshot()["real_stage"]!="幼猫期"
    assert copy.data["inventory"]["water_fountain"]==1
def test_every_request_rereads_profile_even_after_key_rotation(tmp_path):
    received=[]
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            received.append((self.headers.get("Authorization"),json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
            self.send_response(200);self.end_headers();self.wfile.write(b'{"choices":[{"message":{"content":"ok"}}]}')
        def log_message(self,*args):pass
    server=HTTPServer(("127.0.0.1",0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        engine=LifeEngine(tmp_path/"life.json");engine.data["profile"].update(personality="慢热",habits="只喜欢温水")
        vault=SecretVault(tmp_path/"key");vault.save("key-one")
        config={"enabled":True,"base_url":f"http://127.0.0.1:{server.server_port}","model":"test"}
        client=AIClient(config,vault,engine.profile_snapshot);assert client.chat("你好","开心")=="ok"
        first=received[-1][1]["messages"][0]["content"];assert "只喜欢温水" in first and "real_age" in first and "2021-02-28" in first
        engine.data["profile"].update(personality="活泼",habits="午后爱晒太阳");engine.data["birth_date"]="2020-02-29";vault.save("key-two")
        assert client.diary([],"平静")=="ok"
        second=received[-1][1]["messages"][0]["content"]
        assert "午后爱晒太阳" in second and "2020-02-29" in second and "只喜欢温水" not in second
        assert received[-1][0]=="Bearer key-two"
        before=len(received)
        with pytest.raises(ValueError,match="档案"):AIClient(config,vault).chat("绕过","开心")
        assert len(received)==before
    finally:server.shutdown();server.server_close();vault.clear()
def test_every_active_item_has_distinct_physical_art():
    app=QApplication.instance() or QApplication([]);images=[]
    assert not any(v["kind"]=="room" for v in BY_ID.values())
    for id in BY_ID:
        pix=item_pixmap(id,96);assert not pix.isNull() and not pix.mask().isNull()
        images.append(bytes(pix.toImage().constBits()))
    # bowl and food_bowl share the same physical bowl intentionally, all other product silhouettes differ.
    assert len(set(images))>=len(BY_ID)-1
def test_desktop_water_placement_persistence_and_safe_cleanup(tmp_path):
    from niangao.pet import PetWindow
    from niangao.config import Settings
    app=QApplication.instance() or QApplication([]);p=PetWindow(Settings(tmp_path/"settings.json"));p.show()
    count=p.life.data["inventory"]["water_fountain"];assert p.desktop.place("water_fountain",QPoint(100,100))[0]
    uid=next(iter(p.desktop.widgets));w=p.desktop.widgets[uid];assert not w.mask().contains(QPoint(0,0))
    w.down=True;w.move(210,190);p.desktop.repair();assert w.pos()==QPoint(210,190);w.down=False
    first_image=w.compose().toImage();first=bytes(first_image.constBits());w.phase+=.8;second_image=w.compose().toImage();assert bytes(second_image.constBits())!=first
    assert p.desktop.activate(uid) and w.record["water"]==80
    for _ in range(4):
        p.life.cooldowns["water"]=-1e12;assert p.desktop.activate(uid)
    assert w.record["water"]==0 and not p.desktop.activate(uid)
    p.desktop.refill(uid);assert w.record["water"]==100
    w.move(180,180);w.record.update(x=180,y=180);p.desktop.save();p.close();app.processEvents()
    p2=PetWindow(Settings(tmp_path/"settings.json"));assert len(p2.desktop.widgets)==1
    p2.desktop.clear();assert not p2.desktop.widgets and not p2.life.data["desktop_items"]
    assert p2.life.data["inventory"]["water_fountain"]==count
    p2.close();app.processEvents()
def test_profile_editor_and_separate_inventory_pages(tmp_path):
    from niangao.pet import PetWindow
    from niangao.config import Settings
    app=QApplication.instance() or QApplication([]);p=PetWindow(Settings(tmp_path/"settings.json"));p.open_life();ui=p.life_window
    assert ui.width()<=900 and p.bubble.width()<244 and ui.stack.count()==8
    assert not any("3D" in ui.nav.item(i).text() for i in range(8))
    ui.profile_fields["personality"].setPlainText("胆小但亲人");ui.profile_fields["habits"].setPlainText("睡前舔爪")
    ui.save_profile();assert ui.client.profile_provider()["identity"]["personality"]=="胆小但亲人"
    assert ui.shop_container is not ui.bag_container and "water_bowl" in ui.bag_cards
    ui.care("water","idle");assert any(w.id=="water_bowl" for w in p.desktop.widgets.values())
    p.close();app.processEvents()
