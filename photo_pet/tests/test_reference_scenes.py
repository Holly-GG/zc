"""Read-only chapter composition must reflect actual game data and remain usable."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

def test_status_chapter_tracks_existing_state_without_changing_data(tmp_path):
 from niangao.config import Settings
 from niangao.pet import PetWindow
 import copy
 app=QApplication.instance() or QApplication([])
 pet=PetWindow(Settings(tmp_path/'settings.json'));pet.timer.stop();pet.open_life();ui=pet.life_window
 before=copy.deepcopy(pet.life.data);ui.status_chapter.refresh();assert before==pet.life.data
 pet.life.data['stats']['mood']=37;pet.life.data['stats']['health']=72
 pet.life.data['profile']['personality']='安静但好奇'
 ui.refresh();assert ui.status_chapter.rings['mood'].value()==ui.bars['mood'].value()==37
 assert ui.status_chapter.levels['health'].value()==72 and '安静但好奇' in ui.status_chapter.profile.text()
 assert ui.overview_tabs.count()==2 and ui.nav.count()==9
 pet.life.data['events'].extend([{'at':'2020-01-01T12:00:00','day':'2020-01-01','kind':'test','text':'过期事件不应冒充今天'}, {'at':pet.life.today().isoformat()+'T13:00:00','day':pet.life.today().isoformat(),'kind':'test','text':'今日记录应该显示'}])
 ui.status_chapter.refresh();assert '今日记录应该显示' in ui.status_chapter.events.text() and '过期事件' not in ui.status_chapter.events.text()
 for width,height in ((1260,820),(860,650),(740,540)):
  ui.resize(width,height);ui.nav.setCurrentRow(0);ui.overview_tabs.setCurrentIndex(1)
  for _ in range(4):app.processEvents()
  assert ui.stack.widget(0).horizontalScrollBar().maximum()==0
 pet.close();app.processEvents()

def test_scene_assets_and_decorations_are_not_interactive():
 from niangao.art import asset_path
 from niangao.reference_scenes import ScenePortrait,SpecimenStrip
 app=QApplication.instance() or QApplication([])
 for scene in ('home','care','status','diary','backpack','album','settings','chat'):
  image=QImage(str(asset_path('ui/botanical/scene-'+scene+'.webp')))
  assert not image.isNull() and image.width()>=1000 and image.height()>=600
 for widget in (ScenePortrait(),SpecimenStrip()):
  assert widget.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
  assert widget.focusPolicy()==Qt.FocusPolicy.NoFocus
 assert QImage(str(asset_path('ui/botanical/objects.webp'))).hasAlphaChannel()
