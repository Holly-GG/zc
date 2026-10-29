"""Real controls remain reachable in the responsive layered presentation."""
import json,hashlib
from pathlib import Path
from PySide6.QtCore import Qt,QPoint
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication,QPushButton,QLabel

def test_layer_assets_have_integrity():
 from niangao.art import asset_path
 root=asset_path('ui/layers');data=json.loads((root/'manifest.json').read_text())
 for row in data['layers']:
  path=root/row['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
  assert not QImage(str(path)).isNull()
 assert QImage(str(root/'header-ornament.png')).hasAlphaChannel()

def test_nine_pages_fit_and_real_links_navigate(tmp_path):
 from niangao.pet import PetWindow
 from niangao.config import Settings
 app=QApplication.instance() or QApplication([])
 pet=PetWindow(Settings(tmp_path/'settings.json'));pet.timer.stop();pet.open_life();ui=pet.life_window
 assert ui.presentation.currentIndex()==0
 try:
  for width,height in ((740,540),(860,650)):
   ui.resize(width,height)
   for index in range(9):
    ui.nav.setCurrentRow(index)
    for _ in range(3):app.processEvents()
    scroll=ui.stack.widget(index);page=scroll.widget()
    assert page.width()<=scroll.viewport().width(),(index,page.width(),scroll.viewport().width())
    assert scroll.horizontalScrollBar().maximum()==0
    for label in page.findChildren(QLabel,'hero'):
     if label.isVisible():assert label.height()>=label.heightForWidth(label.width()),(index,label.text(),label.size())
    from niangao.journal_components import CardGrid
    for grid in page.findChildren(CardGrid):
     if not grid.isVisible():continue  # Hidden status tab has not been laid out yet.
     for a,card in enumerate(grid.cards):
      for other in grid.cards[a+1:]:assert not card.geometry().intersects(other.geometry()),(index,card.geometry(),other.geometry())
    for button in page.findChildren(QPushButton,'pageLink'):
     assert button.width()>=44 and button.height()>=32
    scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum());app.processEvents()
   ui.nav.setCurrentRow(2);app.processEvents();scroll=ui.stack.widget(2);scroll.verticalScrollBar().setValue(0);app.processEvents()
   link=scroll.widget().findChild(QPushButton,'pageLink');QTest.mouseClick(link,Qt.MouseButton.LeftButton);app.processEvents()
   assert ui.nav.currentRow()==3
   ui.nav.setCurrentRow(5);app.processEvents()
   assert ui.chat_input.isVisible() and ui.chat_send.isVisible()
   assert ui.rect().contains(ui.chat_input.mapTo(ui,QPoint(0,0)))
   assert ui.rect().contains(ui.chat_send.mapTo(ui,ui.chat_send.rect().bottomRight()))
   ui.chat_input.setText('分层界面测试');ui.send_chat()
   assert '分层界面测试' in ui.chat_log.toPlainText() and ui.chat_input.text()==''
 finally:pet.close();app.processEvents()
