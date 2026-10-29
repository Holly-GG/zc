import json,threading
from http.server import BaseHTTPRequestHandler,HTTPServer
from urllib.error import HTTPError
from io import BytesIO
import pytest
from niangao.life.providers import build_request,parse_reply,PRESETS,endpoint
from niangao.life.ai import AIClient,SecretVault,checked_base
from niangao.life.engine import LifeEngine

@pytest.mark.parametrize('base,suffix',[
 ('https://api.deepseek.com/v1','/chat/completions'),
 ('https://api.deepseek.com/v1/chat/completions',''),
 ('https://dashscope.aliyuncs.com/compatible-mode/v1','/chat/completions'),
 ('https://open.bigmodel.cn/api/paas/v4','/chat/completions'),
 ('https://ark.cn-beijing.volces.com/api/v3','/chat/completions'),
 ('https://qianfan.baidubce.com/v2','/chat/completions')])
def test_compatible_endpoints(base,suffix):
 assert endpoint(base,'openai_chat','model')==base+suffix
 assert checked_base('  '+base+'  ')==base # whitespace around input is trimmed

@pytest.mark.parametrize('protocol,response,header',[
 ('openai_chat',{'choices':[{'message':{'content':[{'type':'text','text':'连接成功'}]}}]},'Authorization'),
 ('anthropic',{'content':[{'type':'thinking','thinking':'hidden'},{'type':'text','text':'连接成功'}]},'x-api-key'),
 ('gemini',{'candidates':[{'content':{'parts':[{'text':'秘密思考','thought':True},{'text':'连接成功'}]}}]},'x-goog-api-key'),
 ('openai_responses',{'output':[{'type':'reasoning','summary':[]},{'type':'message','content':[{'type':'output_text','text':'连接成功'}]}]},'Authorization')])
def test_real_http_protocols_and_fresh_profile(tmp_path,protocol,response,header):
 received=[]
 class Handler(BaseHTTPRequestHandler):
  def do_POST(self):
   received.append((self.path,dict(self.headers),json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
   self.send_response(200);self.end_headers();self.wfile.write(json.dumps(response,ensure_ascii=False).encode())
  def log_message(self,*args):pass
 server=HTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  vault=SecretVault(tmp_path/'key');vault.save('test-protocol-key')
  engine=LifeEngine(tmp_path/'life.json');settings=dict(enabled=True,protocol=protocol,base_url=f'http://127.0.0.1:{server.server_port}/v1',model='test-model')
  client=AIClient(settings,vault,engine.profile_snapshot)
  for personality in ('慢热但亲人','活泼但怕吵'):
   engine.data['profile']['personality']=personality
   assert client.test_connection().startswith('连接成功')
   path,headers,body=received[-1];assert any(k.lower()==header.lower() for k in headers)
   assert 'test-protocol-key' not in path and 'test-protocol-key' not in json.dumps(body)
   assert '<NIANGAO_PROFILE>' in json.dumps(body) and personality in json.dumps(body,ensure_ascii=False)
  assert path.endswith({'openai_chat':'/chat/completions','anthropic':'/messages','gemini':'/models/test-model:generateContent','openai_responses':'/responses'}[protocol])
 finally:server.shutdown();server.server_close();vault.clear()

@pytest.mark.parametrize('protocol', ['openai_chat','anthropic','gemini','openai_responses'])
def test_no_profile_no_network_for_all_protocols(tmp_path,protocol):
 client=AIClient(dict(enabled=True,protocol=protocol),SecretVault(tmp_path/'key'))
 with pytest.raises(ValueError,match='档案'):client.test_connection()

def test_reasoning_budget_and_parameter_names():
 messages=[{'role':'system','content':'档案'},{'role':'user','content':'hi'}]
 for model in ('deepseek-reasoner','o3-mini','gpt-5-mini'):
  url,headers,payload,timeout=build_request(dict(protocol='openai_chat',base_url='https://example.com/v1',model=model),messages,'key',True)
  field='max_tokens' if model=='deepseek-reasoner' else 'max_completion_tokens'
  assert payload[field]>=4096 and timeout>=90 and payload['stream'] is False
 for protocol in ('anthropic','gemini','openai_responses'):
  url,_,payload,_=build_request(dict(protocol=protocol,base_url='https://example.com/v1',model='test'),messages,'key',True)
  assert 'key' not in url

@pytest.mark.parametrize('protocol,data',[
 ('openai_chat',{'choices':[]}),('openai_chat',{'choices':{}}),('gemini',{'candidates':[{'content':{'parts':None}}]}),('openai_responses',{'output':None}),('anthropic',{'content':[{'type':'thinking','thinking':'secret'}]}),
 ('gemini',{'candidates':[]}),('openai_responses',{'output':[]}),('openai_chat',[]),
 ('openai_chat',{'choices':[{'message':{'content':None,'reasoning_content':'hidden'}}]})])
def test_empty_or_reasoning_only_is_not_success(protocol,data):
 with pytest.raises(ValueError):parse_reply(data,protocol)

def test_http_errors_do_not_leak_key_or_server_body(tmp_path,monkeypatch):
 class Opener:
  def open(self,req,timeout):raise HTTPError(req.full_url,401,'secret-key',{},BytesIO(b'secret-key'))
 monkeypatch.setattr('urllib.request.build_opener',lambda *args:Opener())
 vault=SecretVault(tmp_path/'key');vault.save('secret-key')
 client=AIClient(dict(enabled=True,base_url='https://example.com/v1',model='test'),vault,LifeEngine(tmp_path/'life.json').profile_snapshot)
 with pytest.raises(ValueError) as error:client.test_connection()
 assert '401' in str(error.value) and 'secret-key' not in str(error.value)

def test_profile_ui_provider_switch_keeps_old_secret_until_save(tmp_path):
 from PySide6.QtWidgets import QApplication
 from niangao.pet import PetWindow
 from niangao.config import Settings
 app=QApplication.instance() or QApplication([]);pet=PetWindow(Settings(tmp_path/'settings.json'));pet.timer.stop();pet.vault.save('old-key');pet.open_life();ui=pet.life_window
 ui.apply_api_preset(1);assert pet.vault.load()=='old-key' and not ui.save_ai()
 ui.key.setText('new-provider-key');assert ui.save_ai();assert pet.life.data['ai']['base_url']=='https://api.deepseek.com/v1'
 assert pet.life.data['ai']['protocol']=='openai_chat' and pet.vault.load()=='new-provider-key'
 pet.close();app.processEvents()
