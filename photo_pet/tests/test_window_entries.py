"""Exercise user-facing entry actions, window recovery and actual pointer navigation."""
from PySide6.QtCore import Qt,QPoint
from PySide6.QtWidgets import QApplication,QPushButton
from PySide6.QtTest import QTest

def test_entries_restore_hidden_and_minimized_windows(tmp_path):
 from niangao.pet import PetWindow
 from niangao.config import Settings
 app=QApplication.instance() or QApplication([]);pet=PetWindow(Settings(tmp_path/'settings.json'));pet.timer.stop()
 try:
  for open_window,name in ((pet.open_life,'life_window'),(pet.open_work,'work_panel'),(pet.open_focus,'focus_panel')):
   open_window();widget=getattr(pet,name);app.processEvents()
   widget.showMinimized();app.processEvents();open_window();app.processEvents()
   assert widget.isVisible() and not widget.isMinimized(),name
   widget.hide();widget.move(-9000,-9000);open_window();app.processEvents()
   assert widget.isVisible() and widget.screen().availableGeometry().intersects(widget.frameGeometry()),name
  ui=pet.life_window;ui.enter_skin();panel=pet.work_panel;panel.open_settings();app.processEvents()
  assert ui.presentation.currentIndex()==0 and ui.nav.currentRow()==7
  panel.search_input.setText('DeepSeek');panel.open_result(panel.search_results.item(0));app.processEvents()
  assert ui.presentation.currentIndex()==0 and ui.nav.currentRow()==7
  ui.resize(740,540);pet.open_life();app.processEvents()
  for i in range(9):
   item=ui.nav.item(i);ui.nav.scrollToItem(item);app.processEvents()
   QTest.mouseClick(ui.nav.viewport(),Qt.MouseButton.LeftButton,pos=ui.nav.visualItemRect(item).center());app.processEvents()
   assert ui.nav.currentRow()==ui.stack.currentIndex()==i
  focus=pet.focus_panel;pet.open_focus();focus.minutes.setValue(1)
  for text,state in (('开始',True),('暂停',False),('继续',True)):
   button=next(b for b in focus.findChildren(QPushButton) if b.text()==text)
   assert button.width()>=44 and focus.rect().contains(button.mapTo(focus,button.rect().bottomRight()))
   QTest.mouseClick(button,Qt.MouseButton.LeftButton);app.processEvents();assert pet.life.data['focus']['active']==state
  panel=pet.work_panel;panel.tabs.setCurrentIndex(0);panel.resize(400,560);pet.open_work();app.processEvents()
  for control in (panel.text,panel.send_button,panel.clear_button):
   assert control.isVisible() and panel.rect().contains(control.mapTo(panel,control.rect().bottomRight()))
  assert panel.text.width()>=180
  ui.show_classic(5);ui.resize(740,540);app.processEvents();ui.nav.verticalScrollBar().setValue(0);app.processEvents()
  assert ui.nav.visualItemRect(ui.nav.item(8)).bottom()<=ui.nav.viewport().rect().bottom()
  pet.life.add_task('检查较长的待办文字能否完整换行并滚动阅读，保留任务内容，不把操作按钮挤出窗口。'*3)
  focus.refresh();app.processEvents()
  last=focus.tasks.count()-1
  assert focus.tasks.item(last).toolTip()==focus.tasks.item(last).text()
  assert focus.tasks.sizeHintForRow(last)>focus.tasks.fontMetrics().height()*2
 finally:pet.close();app.processEvents()
