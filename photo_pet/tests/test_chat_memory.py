import json,threading
from datetime import datetime,timedelta
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler,HTTPServer
import pytest
from niangao.life.chat_store import ChatStore,BudgetExceeded
from niangao.life.token_budget import identity,policy,estimate,usage_from
from niangao.life.calendar_cn import CHINA
from niangao.life.conversations import ChatChannel
from niangao.life.ai import AIClient,SecretVault
from niangao.life.engine import LifeEngine

def test_full_archive_restart_dates_json_and_no_truncation(tmp_path):
 now=[datetime(2026,10,29,23,59,tzinfo=CHINA)];s=ChatStore(tmp_path/'chat.sqlite3',lambda:now[0]);id=s.session('work','provider','test')
 text='完整历史年糕'*5000;u=s.append(id,'user',text,'api','pending');s.complete_turn(u,id,'完整回复'*4000)
 now[0]+=timedelta(minutes=2);s.append(id,'user','第二天','local')
 reloaded=ChatStore(s.path);assert reloaded.transcript(id)[0]['content']==text
 assert len(reloaded.by_day('2026-10-29'))==2 and len(reloaded.by_day('2026-10-30'))==1
 snapshot=json.loads((tmp_path/'chat_sessions'/f'{id}.json').read_text(encoding='utf-8'));assert snapshot['messages'][0]['content']==text
 reloaded.export_json(tmp_path/'all.json');assert len(json.loads((tmp_path/'all.json').read_text(encoding='utf-8'))['messages'])==3

def test_daily_reservations_are_atomic_and_reset_by_china_day(tmp_path):
 now=[datetime(2026,10,29,23,59,59,tzinfo=CHINA)];s=ChatStore(tmp_path/'chat.sqlite3',lambda:now[0])
 def reserve(_):
  try:return s.reserve('model','chat',600,1000)
  except BudgetExceeded:return None
 with ThreadPoolExecutor(max_workers=2) as pool:ids=list(pool.map(reserve,range(2)))
 assert sum(v is not None for v in ids)==1 and s.daily()['total']==600
 good=next(v for v in ids if v);s.finish(good,{'input':100,'output':20,'total':120});assert s.daily()=={'total':120,'actual':120,'estimated':0}
 now[0]+=timedelta(seconds=2);assert s.daily()['total']==0
 assert s.reserve('model','summary',900,1000)

def test_model_context_profiles_are_independent_and_persist(tmp_path):
 e=LifeEngine(tmp_path/'life.json');a=dict(e.data['ai'],base_url='https://api.deepseek.com/v1',model='deepseek-chat');b=dict(a,model='other')
 e.data['ai']['context_profiles'][identity(a)]={'window':128000,'threshold':110000,'keep':6};e.save()
 e2=LifeEngine(e.path);a['context_profiles']=e2.data['ai']['context_profiles'];b['context_profiles']=e2.data['ai']['context_profiles']
 assert policy(a)['threshold']==110000 and identity(a)!=identity(b)
 assert policy(dict(b,base_url='https://example.com'))['window']==32768

def test_estimate_covers_system_summary_and_recent_messages():
 one=estimate([{'role':'user','content':'hello'}]);many=estimate([{'role':'system','content':'档案'*100},{'role':'user','content':'hello'}])
 assert many['conservative']>one['conservative'] and many['estimated']>one['estimated']

@pytest.mark.parametrize('protocol,payload,total',[
 ('openai_chat',{'usage':{'prompt_tokens':100,'completion_tokens':30,'total_tokens':130,'completion_tokens_details':{'reasoning_tokens':20}}},130),
 ('anthropic',{'usage':{'input_tokens':20,'cache_creation_input_tokens':30,'cache_read_input_tokens':40,'output_tokens':10}},100),
 ('gemini',{'usageMetadata':{'promptTokenCount':10,'candidatesTokenCount':5,'thoughtsTokenCount':12,'totalTokenCount':27}},27),
 ('openai_responses',{'usage':{'input_tokens':20,'output_tokens':10,'total_tokens':30}},30)])
def test_usage_does_not_double_count_hidden_reasoning(protocol,payload,total):assert usage_from(payload,protocol)['total']==total

@pytest.fixture
def server():
 seen=[]
 class Handler(BaseHTTPRequestHandler):
  def do_POST(self):
   body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));seen.append(body)
   summary='整理为简短承接摘要' in json.dumps(body,ensure_ascii=False) or '将各段摘要合并' in json.dumps(body,ensure_ascii=False)
   text='用户喜欢年糕，待办是写报告，保留已知事实。' if summary else '这是新会话的回复'
   self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'choices':[{'message':{'content':text}}],'usage':{'prompt_tokens':100,'completion_tokens':20,'total_tokens':120}},ensure_ascii=False).encode())
  def log_message(self,*args):pass
 http=HTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=http.serve_forever,daemon=True).start()
 yield f'http://127.0.0.1:{http.server_port}/v1',seen
 http.shutdown();http.server_close()

def setup(tmp_path,base):
 engine=LifeEngine(tmp_path/'life.json');vault=SecretVault(tmp_path/'key');vault.save('local-test-key')
 settings=dict(engine.data['ai'],enabled=True,base_url=base,model='test')
 client=AIClient(settings,vault,engine.profile_snapshot);channel=ChatChannel(client.store,'work');channel.select(settings)
 return client,channel

def test_rollover_summarizes_forks_and_keeps_every_original(tmp_path,server):
 base,seen=server;client,c=setup(tmp_path,base);old=c.session_id
 client.settings['context_profiles']={identity(client.settings):{'window':16000,'threshold':6000,'keep':4}}
 for i in range(16):client.store.append(old,'user' if i%2==0 else 'assistant',f'第{i}段 '+'猫'*160,'api')
 assert c.send(client,'继续写报告','开心')=='这是新会话的回复'
 assert c.last_rollover and c.session_id!=old and len(seen)>=2
 new=client.store.get_session(c.session_id);assert new['parent']==old and '喜欢年糕' in new['summary']
 assert all(client.store.transcript(old,100)[i]['content'].startswith(f'第{i}段') for i in range(16))
 assert '<NIANGAO_PROFILE>' in json.dumps(seen[-1]) and '喜欢年糕' in json.dumps(seen[-1],ensure_ascii=False)
 assert client.store.daily()['actual']==120*len(seen)
 assert (tmp_path/'chat_sessions'/f'{old}.json').exists() and (tmp_path/'chat_sessions'/f'{c.session_id}.json').exists()

def test_more_than_eight_messages_are_sent_without_silent_history_cut(tmp_path,server):
 base,seen=server;client,c=setup(tmp_path,base)
 for i in range(20):client.store.append(c.session_id,'user' if i%2==0 else 'assistant',f'历史消息{i}','api')
 c.send(client,'现在的问题','开心');assert len(seen[-1]['messages'])==22
 assert '历史消息0' in json.dumps(seen[-1],ensure_ascii=False)

def test_daily_budget_stops_before_http_and_keeps_failed_user_message(tmp_path,server):
 base,seen=server;client,c=setup(tmp_path,base);client.settings['daily_token_limit']=1000
 with pytest.raises(BudgetExceeded):c.send(client,'这条必须保留','开心')
 assert not seen and client.store.transcript(c.session_id)[0]['state']=='failed'
 assert client.store.transcript(c.session_id)[0]['content']=='这条必须保留'

def test_light_thinking_blocks_reasoner_without_calling_server(tmp_path,server):
 base,seen=server;client,c=setup(tmp_path,base);client.settings['model']='deepseek-reasoner'
 with pytest.raises(ValueError,match='深度思考'):c.send(client,'hello','开心')
 assert not seen and client.store.daily()['total']==0

def test_history_pagination_can_read_all_messages(tmp_path):
 s=ChatStore(tmp_path/'chat.sqlite3');id=s.session('main','test','model')
 for i in range(105):s.append(id,'user',str(i),'local')
 day=s.now().date().isoformat();assert len(s.by_day(day))==100 and len(s.by_day(day,100))==5
 assert s.by_day(day,100)[-1]['content']=='104'

def test_summary_failure_preserves_original_and_does_not_create_new_session(tmp_path,monkeypatch):
 client,c=setup(tmp_path,'https://example.com/v1');old=c.session_id
 client.settings['context_profiles']={identity(client.settings):{'window':16000,'threshold':6000,'keep':4}}
 for i in range(16):client.store.append(old,'user' if i%2==0 else 'assistant','旧内容'+str(i)+'猫'*180,'api')
 monkeypatch.setattr(AIClient,'request',lambda *args,**kwargs:(_ for _ in ()).throw(ValueError('摘要服务暂不可用')))
 with pytest.raises(ValueError,match='摘要'):c.send(client,'待发送的内容','开心')
 assert c.session_id==old and len(client.store.list_sessions('work'))==1
 assert all(client.store.transcript(old,100)[i]['content'].startswith('旧内容'+str(i)) for i in range(16))
 assert any(row['state']=='failed' and row['content']=='待发送的内容' for row in client.store.transcript(old,100))

def test_unknown_billing_reservation_survives_restart_and_cross_midnight(tmp_path):
 now=[datetime(2026,10,29,23,59,59,tzinfo=CHINA)];s=ChatStore(tmp_path/'chat.sqlite3',lambda:now[0]);id=s.reserve('model','summary',1000,2000)
 s.finish(id);s2=ChatStore(s.path,lambda:now[0]);assert s2.daily()['estimated']==1000
 now[0]+=timedelta(seconds=2);assert s2.daily()['total']==0
 s2.finish(id,{'input':200,'output':10,'total':210});assert s2.daily('2026-10-29')['actual']==210 and s2.daily()['total']==0

def test_light_policy_uses_vendor_controls_and_cannot_be_disabled():
 from niangao.life.providers import build_request
 messages=[{'role':'user','content':'hi'}]
 for protocol,base,model in [('openai_chat','https://api.deepseek.com/v1','deepseek-chat'),('openai_chat','https://api.openai.com/v1','gpt-5-mini'),('gemini','https://generativelanguage.googleapis.com/v1beta','gemini-2.5-flash')]:
  _,_,body,_=build_request(dict(protocol=protocol,base_url=base,model=model,max_tokens=16000,light_thinking=False),messages,'key')
  if model=='deepseek-chat':assert body['thinking']['type']=='disabled' and body['max_tokens']<=2048
  if model=='gpt-5-mini':assert body['reasoning_effort']=='low' and body['max_completion_tokens']<=2048
  if protocol=='gemini':assert body['generationConfig']['thinkingConfig']['thinkingBudget']==0
 with pytest.raises(ValueError,match='深度思考'):build_request(dict(protocol='openai_chat',base_url='https://example.com',model='deepseek-reasoner',light_thinking=False),messages,'key')

def test_new_session_does_not_delete_old_history_in_ui(tmp_path):
 from PySide6.QtWidgets import QApplication
 from niangao.pet import PetWindow
 from niangao.config import Settings
 app=QApplication.instance() or QApplication([]);p=PetWindow(Settings(tmp_path/'settings.json'));p.timer.stop();p.set_work_mode(True);p.open_work();w=p.work_panel
 w.text.setText('这条记录必须长期保留');w.send();old=w.channel.session_id;w.clear_chat()
 assert w.channel.session_id!=old and len(p.chat_store.transcript(old))==2
 records=p.chat_store.by_day(p.life.today().isoformat());assert any(r['content']=='这条记录必须长期保留' for r in records)
 w.archive.reset();assert w.archive.rows.count()==2 and '估算' in w.token_meter.text()
 p.close();app.processEvents()

def test_context_and_daily_controls_save_per_model_and_ignore_wheel(tmp_path):
 from PySide6.QtWidgets import QApplication
 from PySide6.QtCore import QPoint,QPointF,Qt
 from PySide6.QtGui import QWheelEvent
 from niangao.pet import PetWindow
 from niangao.config import Settings
 app=QApplication.instance() or QApplication([]);p=PetWindow(Settings(tmp_path/'settings.json'));p.timer.stop();p.open_life();ui=p.life_window
 ui.model.setText('model-a');ui.load_context_profile();ui.context_window.setValue(32768);ui.context_threshold.setValue(20000);ui.daily_tokens.setValue(8000)
 wheel=QWheelEvent(QPointF(4,4),QPointF(4,4),QPoint(),QPoint(0,120),Qt.MouseButton.NoButton,Qt.KeyboardModifier.NoModifier,Qt.ScrollPhase.NoScrollPhase,False)
 app.sendEvent(ui.daily_tokens,wheel);assert ui.daily_tokens.value()==8000 and ui.save_ai()
 ui.model.setText('model-b');ui.load_context_profile();ui.context_window.setValue(64000);ui.context_threshold.setValue(50000);assert ui.save_ai()
 ui.model.setText('model-a');ui.load_context_profile();assert ui.context_threshold.value()==20000
 restored=LifeEngine(p.life.path);assert len(restored.data['ai']['context_profiles'])==2 and restored.data['ai']['daily_token_limit']==8000
 p.close();app.processEvents()
