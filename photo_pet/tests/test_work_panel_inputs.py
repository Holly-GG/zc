import json,threading
from http.server import BaseHTTPRequestHandler,HTTPServer
import pytest
from PySide6.QtCore import Qt,QPoint,QPointF
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

@pytest.fixture(scope='module')
def pet(tmp_path_factory):
 from niangao.pet import PetWindow
 from niangao.config import Settings
 app=QApplication.instance() or QApplication([])
 p=PetWindow(Settings(tmp_path_factory.mktemp('work-inputs')/'settings.json'));p.timer.stop();p.show()
 yield p
 p.close();app.processEvents()

def test_settings_choices_ignore_wheel_but_accept_mouse_selection(pet):
 pet.open_life();ui=pet.life_window;ui.nav.setCurrentRow(7);app=QApplication.instance()
 for combo in (ui.api_presets,ui.api_protocol,ui.sound_choice):
  before=combo.currentIndex()
  wheel=QWheelEvent(QPointF(8,8),QPointF(combo.mapToGlobal(QPoint(8,8))),QPoint(),QPoint(0,-120),Qt.MouseButton.NoButton,Qt.KeyboardModifier.NoModifier,Qt.ScrollPhase.NoScrollPhase,False)
  app.sendEvent(combo,wheel);assert combo.currentIndex()==before
  QTest.keyClick(combo,Qt.Key.Key_Down);assert combo.currentIndex()==before
 combo=ui.api_protocol;combo.showPopup();app.processEvents();index=combo.model().index(1,0)
 QTest.mouseClick(combo.view().viewport(),Qt.MouseButton.LeftButton,pos=combo.view().visualRect(index).center());app.processEvents()
 assert combo.currentData()=='openai_responses'

def test_enter_work_mode_shows_chat_input_and_search(pet):
 app=QApplication.instance();pet.set_work_mode(True);app.processEvents();panel=pet.work_panel
 assert panel is not None and panel.isVisible() and panel.text.isVisible() and panel.send_button.isVisible()
 assert panel.tabs.tabText(0)=='API 对话' and panel.tabs.tabText(1)=='应用搜索'
 panel.close();assert not panel.isVisible();pet.open_work();assert panel.isVisible()

def test_local_search_routes_features_items_and_tasks(pet):
 from niangao.work_search import search
 panel=pet.work_panel;pet.life.add_task('完成报告后喝水')
 rows=search('喝水',pet.life.data['tasks']);assert any(r['kind']=='task' for r in rows) and any(r['kind']=='page' for r in rows)
 assert any(r['kind']=='item' for r in search('猫砂'))
 panel.tabs.setCurrentIndex(1);panel.search_input.setText('DeepSeek');assert panel.search_results.count()
 panel.open_result(panel.search_results.item(0));assert pet.life_window.nav.currentRow()==7
 assert not search('不存在xyzabcdefgh',pet.life.data['tasks'])
 panel.tabs.setCurrentIndex(0)

def test_work_chat_sends_real_http_and_latest_profile(pet):
 received=[]
 class Handler(BaseHTTPRequestHandler):
  def do_POST(self):
   received.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
   self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'choices':[{'message':{'content':'桌面 API 测试回复'}}]},ensure_ascii=False).encode())
  def log_message(self,*args):pass
 server=HTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  panel=pet.work_panel;pet.life.data['ai'].update(enabled=True,protocol='openai_chat',base_url=f'http://127.0.0.1:{server.server_port}/v1',model='test');pet.vault.save('work-panel-test-key');pet.life.data['profile']['personality']='安静但亲人'
  panel.text.setText('你好年糕');QTest.keyClick(panel.text,Qt.Key.Key_Return)
  assert panel.busy
  panel.send() # Enter cannot queue a second billable request while busy.
  for _ in range(200):
   QTest.qWait(10)
   if not panel.busy:break
  assert len(received)==1 and '安静但亲人' in json.dumps(received[0],ensure_ascii=False)
  assert '[API] 桌面 API 测试回复' in panel.log.toPlainText() and panel.send_button.isEnabled()
  assert panel.history[-1]['content']=='桌面 API 测试回复'
 finally:server.shutdown();server.server_close();pet.life.data['ai']['enabled']=False

def test_work_chat_failure_keeps_input_and_is_not_reported_as_local_success(pet,monkeypatch):
 import niangao.life.jobs
 panel=pet.work_panel;pet.life.data['ai']['enabled']=True
 monkeypatch.setattr(niangao.life.jobs,'run_job',lambda work,done,failed:failed('API HTTP 401：密钥无效'))
 panel.text.setText('这条需要重试');panel.send()
 assert not panel.busy and panel.text.text()=='这条需要重试' and '401' in panel.status.text()
 assert '这条没有收到 API 回复' in panel.log.toPlainText()
 pet.life.data['ai']['enabled']=False
