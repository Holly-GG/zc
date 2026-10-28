from datetime import date
import json,threading
from http.server import HTTPServer,BaseHTTPRequestHandler
import pytest
from niangao.life.age import age_info
from niangao.life.engine import LifeEngine
from niangao.life.layout import valid_placement
from niangao.life.ai import SecretVault,AIClient,checked_base
@pytest.fixture
def clock():return [1000.,1760000000.]
@pytest.fixture
def engine(tmp_path,clock):return LifeEngine(tmp_path/"life.json",lambda:clock[0],lambda:clock[1])
@pytest.mark.parametrize("day,stage",[("2021-05-27","奶猫期"),("2021-05-28","幼猫期"),("2022-02-28","青年成猫"),("2028-02-28","中年成猫"),("2031-02-28","老年猫")])
def test_age_boundaries(day,stage):assert age_info("2021-02-28",date.fromisoformat(day))["stage"]==stage
def test_leap_and_virtual_age():
    a=age_info("2020-02-29",date(2021,2,28),6)
    assert (a["years"],a["months"],a["days"])==(1,0,0)
    assert a["stage"]=="幼猫期" and a["total_months"]==12
def test_future_birthday_rejected():
    with pytest.raises(ValueError):age_info("2099-01-01",date(2026,1,1))
def test_care_cooldown(engine,clock):
    engine.data["stats"]["mood"]=50
    assert engine.care("pet")[0];assert not engine.care("pet")[0];assert engine.data["stats"]["mood"]==55
    clock[0]+=21;assert engine.care("pet")[0]
def test_shop_transaction(engine):
    engine.data["coins"]=10000
    before=engine.data["coins"];assert not engine.buy("bow")[0];assert engine.data["coins"]==before
    assert engine.buy("fish")[0];assert engine.data["coins"]<before
    stock=engine.data["inventory"]["fish"];assert engine.use("fish")[0];assert engine.data["inventory"]["fish"]==stock-1
    engine.data["coins"]=0;stock=engine.data["inventory"]["fish"];assert not engine.buy("fish")[0];assert stock==engine.data["inventory"]["fish"]
def test_task_reward_exactly_once(engine):
    engine.add_task("休息一下");task=engine.data["tasks"][0];coins=engine.data["coins"]
    assert engine.complete_task(task["id"]);assert not engine.complete_task(task["id"]);assert engine.data["coins"]==coins+5
def test_focus_real_time_once_and_restart(engine,clock):
    engine.focus_start(1);clock[0]+=10;engine.tick();engine.focus_pause();assert engine.data["focus"]["remaining"]==50
    clock[0]+=100;engine.tick();assert engine.data["focus"]["remaining"]==50
    engine.focus_resume();clock[0]+=51;coins=engine.data["coins"];engine.tick();engine.tick();assert engine.data["coins"]==coins+20
    engine.focus_start(1);engine.save();other=LifeEngine(engine.path,lambda:clock[0],lambda:clock[1]);assert not other.data["focus"]["active"]
def test_checkin_and_travel(engine,clock):
    assert engine.checkin()[0];assert not engine.checkin()[0]
    assert engine.start_trip()[0];assert not engine.start_trip()[0];clock[1]+=301;engine.tick();assert len(engine.data["postcards"])==1
    engine.tick();assert len(engine.data["postcards"])==1
def test_diary_and_roundtrip(engine,clock):
    engine.care("brush");body=engine.local_diary();assert "梳理" in body
    engine.data["diaries"][engine.today().isoformat()]["note"]="手写内容";engine.local_diary();engine.save()
    other=LifeEngine(engine.path,lambda:clock[0],lambda:clock[1]);assert other.data["diaries"][engine.today().isoformat()]["note"]=="手写内容"
def test_corrupt_and_bad_numeric(tmp_path):
    path=tmp_path/"x.json";path.write_text("{bad");assert LifeEngine(path).error
    path.write_text('{"stats":{"mood":"bad"},"coins":null,"inventory":[],"birth_date":"bad"}')
    e=LifeEngine(path);assert e.save();assert e.data["stats"]["mood"]<=80
def test_furniture_collision_and_reserved_cat():
    bed=dict(id="one",type="bed",x=0,z=0,rotation=0,scale=1)
    assert not valid_placement(bed,[])[0]
    bed["x"]=2;assert valid_placement(bed,[])[0]
    assert not valid_placement(dict(bed,id="two"),[bed])[0]
    assert not valid_placement(dict(bed,x=3.6,scale=1.8),[])[0]
    assert valid_placement(dict(bed,rotation=90),[bed])[0]
def test_vault_no_plaintext(tmp_path):
    v=SecretVault(tmp_path/"secret.dpapi");v.save("unit-test-key");assert v.load()=="unit-test-key"
    if v.path.exists():assert b"unit-test-key" not in v.path.read_bytes()
    v.clear();assert not v.load()
@pytest.mark.parametrize("url",["http://example.com/v1","https://user:pass@example.com","https://example.com?key=secret"])
def test_reject_insecure_api(url):
    with pytest.raises(ValueError):checked_base(url)
def test_api_optin_mock_and_redirect(tmp_path):
    received=[]
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            received.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            if self.path.startswith("/redirect"):
                self.send_response(307);self.send_header("Location","https://example.com/");self.end_headers();return
            self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(b'{"choices":[{"message":{"content":"hello"}}]}')
        def log_message(self,*args):pass
    server=HTTPServer(("127.0.0.1",0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        vault=SecretVault(tmp_path/"key");vault.save("test-key");settings=dict(enabled=False,base_url=f"http://127.0.0.1:{server.server_port}/v1",model="test")
        client=AIClient(settings,vault)
        with pytest.raises(ValueError):client.chat("hi","开心")
        assert not received;settings["enabled"]=True;assert client.chat("hi","开心")=="hello";assert received[-1]["messages"][-1]["content"]=="hi"
        settings["base_url"]=f"http://127.0.0.1:{server.server_port}/redirect"
        with pytest.raises(ValueError,match="重定向"):client.chat("hi","开心")
    finally:server.shutdown();server.server_close();vault.clear()
