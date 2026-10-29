import hashlib,json,zipfile
from pathlib import Path
import pytest
from PySide6.QtCore import Qt,QPoint
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from niangao.skin_pack import SkinPack,import_skin_zip
from niangao.skin_view import rect

ROOT=Path(__file__).resolve().parents[2]

def test_all_eight_original_images_preserve_every_decoded_pixel():
 pack=SkinPack.bundled();manifest=json.loads((pack.root/'provenance.json').read_text(encoding='utf-8'))
 assert len(manifest)==8
 with zipfile.ZipFile(ROOT/'docs/design-system/reference-originals.zip') as z:
  for row in manifest:
   raw=z.read(row['zip_entry']);assert hashlib.sha256(raw).hexdigest()==row['original_sha256']
   source=QImage.fromData(raw).convertToFormat(QImage.Format.Format_RGBA8888)
   rendered=QImage(str(pack.pages[row['page']])).convertToFormat(QImage.Format.Format_RGBA8888)
   assert source.size()==rendered.size() and bytes(source.constBits())==bytes(rendered.constBits())

def test_import_original_zip_is_atomic_and_keeps_original_bytes(tmp_path):
 source=ROOT/'docs/design-system/reference-originals.zip';pack=import_skin_zip(source,tmp_path)
 assert SkinPack.active(tmp_path).root==pack.root
 old=(tmp_path/'page-skins/active.json').read_bytes()
 invalid=tmp_path/'missing.zip'
 with zipfile.ZipFile(invalid,'w') as z:z.writestr('../run.exe',b'not executed')
 with pytest.raises(ValueError):import_skin_zip(invalid,tmp_path)
 assert old==(tmp_path/'page-skins/active.json').read_bytes() and not (tmp_path/'run.exe').exists()
 with zipfile.ZipFile(source) as z:
  manifest=json.loads((SkinPack.bundled().root/'provenance.json').read_text(encoding='utf-8'))
  for row in manifest:assert pack.pages[row['page']].read_bytes()==z.read(row['zip_entry'])

def test_fullpage_navigation_real_typing_profile_save_and_portal_restore(tmp_path):
 from niangao.config import Settings
 from niangao.pet import PetWindow
 app=QApplication.instance() or QApplication([]);pet=PetWindow(Settings(tmp_path/'settings.json'));pet.timer.stop();pet.open_life();ui=pet.life_window;view=ui.skin_view
 assert ui.presentation.currentIndex()==0
 ui.enter_skin()
 def click(key):
  point=view.mapFromScene(rect(view.hotspots[key][1]).center());QTest.mouseClick(view.viewport(),Qt.MouseButton.LeftButton,pos=point);app.processEvents()
 assert ui.presentation.currentIndex()==1 and view.page=='home'
 for width,height in ((1200,751),(860,650),(740,540)):
  ui.resize(width,height);app.processEvents()
  click('nav-chat');assert view.page=='chat'
  field=view.widget_point(ui.chat_input);QTest.mouseClick(view.viewport(),Qt.MouseButton.LeftButton,pos=view.viewport().mapFromGlobal(field))
  QTest.keyClicks(view.viewport(),'skin-'+str(width));QTest.keyClick(view.viewport(),Qt.Key.Key_Return);app.processEvents()
  assert 'skin-'+str(width) in ui.chat_log.toPlainText() and ui.chat_input.text()==''
  click('nav-settings');assert view.page=='settings'
  ui.profile_fields['personality'].setPlainText('温柔而好奇');click('profile-save')
  assert pet.life.data['profile']['personality']=='温柔而好奇'
  for page in ('home','chat','diary','album','backpack','care','status','settings'):
   view.show_page(page);app.processEvents();assert view.page==page
  if width==1200:
   view.show_page('backpack');app.processEvents();point=view.viewport().mapFromGlobal(view.rect_point(view.drag_rects['fish']))
   QTest.mousePress(view.viewport(),Qt.MouseButton.LeftButton,pos=point);QTest.mouseMove(view.viewport(),point+QPoint(18,18));QTest.mouseMove(view.viewport(),QPoint(-60,150));QTest.mouseRelease(view.viewport(),Qt.MouseButton.LeftButton,pos=QPoint(-60,150));app.processEvents()
   assert any(w.id=='fish' for w in pet.desktop.widgets.values());pet.desktop.clear()
  ui.show_classic(5);app.processEvents()
  assert ui.chat_input.parentWidget() is not None and ui.chat_input.graphicsProxyWidget() is None and ui.chat_send.text()=='发送'
  ui.enter_skin();app.processEvents()
 pet.close();app.processEvents()
