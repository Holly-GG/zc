import hashlib,os,struct
from datetime import datetime
from pathlib import Path
import pytest
from PySide6.QtCore import QDate
from PySide6.QtGui import QImage,QColor
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from niangao.life.album import AlbumStore,photo_date,MAX_BYTES
from niangao.life.calendar_cn import CHINA

@pytest.fixture(scope='module',autouse=True)
def app():return QApplication.instance() or QApplication([])

def picture(path,color='#77AAD7',format='PNG'):
 image=QImage(120,80,QImage.Format.Format_RGB32);image.fill(QColor(color));assert image.save(str(path),format);return path

def add_exif(path,day,orientation=1):
 text=(day.replace('-',':')+' 12:34:56\0').encode()
 tiff=b'II'+struct.pack('<HI',42,8)+struct.pack('<H',2)
 tiff+=struct.pack('<HHI',0x112,3,1)+struct.pack('<H',orientation)+b'\0\0'
 tiff+=struct.pack('<HHII',0x8769,4,1,38)+b'\0'*4
 tiff+=struct.pack('<H',1)+struct.pack('<HHII',0x9003,2,len(text),56)+b'\0'*4+text
 payload=b'Exif\0\0'+tiff;raw=path.read_bytes();path.write_bytes(raw[:2]+b'\xff\xe1'+struct.pack('>H',len(payload)+2)+payload+raw[2:])

def test_exif_date_original_copy_and_orientation(tmp_path):
 source=picture(tmp_path/'年糕.jpg',format='JPEG');add_exif(source,'2024-02-29',6);raw=source.read_bytes()
 store=AlbumStore(tmp_path/'album');id,new=store.import_one(source);record=store.get(id)
 assert new and record['day']=='2024-02-29' and record['date_source']=='拍摄日期（EXIF）'
 assert record['original'].startswith('2024-02-29/') and store.owned(record['original']).read_bytes()==raw==source.read_bytes()
 thumb=QImage(str(store.owned(record['thumbnail'])));assert not thumb.isNull() and thumb.height()>thumb.width()
 assert record['sha256']==hashlib.sha256(raw).hexdigest()

def test_file_date_fallback_manual_date_and_restart(tmp_path):
 source=picture(tmp_path/'photo.png');stamp=datetime(2022,7,8,22,0,tzinfo=CHINA).timestamp();os.utime(source,(stamp,stamp))
 assert photo_date(source)==('2022-07-08','文件修改日期')
 store=AlbumStore(tmp_path/'album');id,_=store.import_one(source,'2026-10-29');assert store.get(id)['date_source']=='手动指定日期'
 source.unlink();reloaded=AlbumStore(store.root);rows,total=reloaded.query(month='2026-10');assert total==1 and rows[0]['id']==id
 assert reloaded.owned(rows[0]['original']).exists()

def test_duplicate_partial_failure_no_source_mutation(tmp_path):
 good=picture(tmp_path/'good.png');duplicate=tmp_path/'renamed.png';duplicate.write_bytes(good.read_bytes());bad=tmp_path/'bad.jpg';bad.write_text('not an image')
 store=AlbumStore(tmp_path/'album');result=store.import_files([good,duplicate,bad],override='2026-01-01')
 assert len(result['imported'])==len(result['duplicates'])==len(result['errors'])==1
 assert store.query()[1]==1 and good.exists() and bad.exists() and not list(store.root.glob('*.tmp'))

def test_move_search_export_remove_keeps_source(tmp_path):
 source=picture(tmp_path/'source.png');store=AlbumStore(tmp_path/'album');id,_=store.import_one(source,'2026-10-01');old=store.owned(store.get(id)['original'])
 store.update(id,'午后的年糕','2025-12-31','午睡','日记里的阳光');record=store.get(id)
 assert not old.exists() and record['original'].startswith('2025-12-31/')
 assert store.query(month='2025-12',category='午睡',search='阳光')[1]==1
 assert store.query(month='2026-10')[1]==0 and store.months()==[('2025-12',1)]
 target=tmp_path/'export.png';store.export_original(id,target);assert target.read_bytes()==source.read_bytes()
 managed=store.owned(record['original']);store.remove(id);assert source.exists() and target.exists() and not managed.exists() and store.get(id) is None

def test_invalid_date_path_and_large_file_no_records(tmp_path):
 store=AlbumStore(tmp_path/'album');source=picture(tmp_path/'source.png')
 with pytest.raises(ValueError):store.import_one(source,'2026-02-30')
 with pytest.raises(ValueError):store.owned('../source.png')
 huge=tmp_path/'large.jpg'
 with huge.open('wb') as stream:stream.truncate(MAX_BYTES+1)
 with pytest.raises(ValueError):store.import_one(huge)
 assert store.query()[1]==0 and source.exists()

def test_corrupt_exif_fallback_still_archives(tmp_path):
 source=picture(tmp_path/'bad-exif.jpg',format='JPEG');add_exif(source,'xxxx-xx-xx')
 assert photo_date(source)[1]=='文件修改日期'
 assert AlbumStore(tmp_path/'album').import_one(source)[1]

def test_pagination_and_sort(tmp_path):
 store=AlbumStore(tmp_path/'album')
 for i in range(14):store.import_one(picture(tmp_path/f'{i}.png',QColor.fromHsv(i*15,100,230).name()),f'2026-10-{i+1:02d}')
 first,count=store.query();second,_=store.query(offset=12);assert count==14 and len(first)==12 and len(second)==2
 assert not ({r['id'] for r in first}&{r['id'] for r in second})
 assert first[0]['day']=='2026-10-14' and store.query(ascending=True)[0][0]['day']=='2026-10-01'

def test_update_failure_restores_original_folder(tmp_path,monkeypatch):
 store=AlbumStore(tmp_path/'album');id,_=store.import_one(picture(tmp_path/'source.png'),'2026-10-01');old=store.owned(store.get(id)['original'])
 from contextlib import contextmanager
 original=store.db;calls=[0]
 @contextmanager
 def broken():
  calls[0]+=1
  if calls[0]>1:raise OSError('disk full')
  with original() as db:yield db
 monkeypatch.setattr(store,'db',broken)
 with pytest.raises(OSError):store.update(id,'new','2026-11-01','日常')
 assert old.exists() and not list((store.root/'2026-11-01').glob('*'))

def test_album_ui_import_filter_navigation_and_sizes(tmp_path,app):
 from niangao.config import Settings
 from niangao.pet import PetWindow
 from niangao.typography import install_fonts
 assert set(install_fonts(app))=={'body','title','script'}
 pet=PetWindow(Settings(tmp_path/'profile/settings.json'));pet.timer.stop();pet.open_life();ui=pet.life_window
 assert ui.stack.count()==9 and ui.nav.item(7).text()=='性格与设置' and ui.nav.item(8).text()=='宠物相册'
 ui.nav.setCurrentRow(8);app.processEvents();album=ui.album_widget
 album.manual.setChecked(True);album.day.setDate(QDate(2024,2,29));source=picture(tmp_path/'uploaded.png')
 album.import_paths([str(source)]);assert album.busy and not album.import_button.isEnabled()
 for _ in range(300):
  QTest.qWait(10)
  if not album.busy:break
 assert not album.busy and len(album.last_result['imported'])==1 and album.month.findData('2024-02')>=0
 album.month.setCurrentIndex(album.month.findData('2024-02'));assert len(album.grid.cards)==1 and source.exists()
 album.search.setText('不匹配');QTest.qWait(250);assert album.empty.isVisible()
 for width,height in ((740,540),(860,650)):
  ui.resize(width,height)
  for i in range(9):
   ui.nav.setCurrentRow(i);app.processEvents();assert ui.stack.widget(i).horizontalScrollBar().maximum()==0,(width,i)
 pet.close();app.processEvents()

def test_font_bundle_manifest_and_root_zip():
 import json,zipfile
 repository=Path(__file__).resolve().parents[2];folder=repository/'fonts'
 for record in json.loads((folder/'manifest.json').read_text(encoding='utf-8')):
  assert hashlib.sha256((folder/record['file']).read_bytes()).hexdigest()==record['sha256']
 with zipfile.ZipFile(repository/'Niangao-Fonts.zip') as z:
  assert z.testzip() is None
  for file in ('NiangaoSans.ttf','NiangaoSerif.ttf','NiangaoScript.ttf','roles.json','NotoSansSC-OFL.txt','NotoSerifSC-OFL.txt','Allura-OFL.txt'):assert 'fonts/'+file in z.namelist()

def test_font_roles_reject_paths_and_invalid_sizes(tmp_path,monkeypatch):
 import json
 from niangao import typography
 (tmp_path/'roles.json').write_text(json.dumps({'body':{'family':'evil; color:red','file':'../font.ttf','size':99},'title':{'family':'Example Serif','file':'safe.ttf','size':26}}),encoding='utf-8')
 monkeypatch.setattr(typography,'font_directory',lambda:tmp_path)
 roles=typography.roles();assert roles['body']==typography.DEFAULT['body'] and roles['title']=={'family':'Example Serif','file':'safe.ttf','size':26}

def test_cancel_import_preserves_source_and_leaves_no_partial_copy(tmp_path):
 import threading
 source=picture(tmp_path/'source.png');store=AlbumStore(tmp_path/'album');cancel=threading.Event();cancel.set()
 result=store.import_files([source],cancel=cancel);assert result['cancelled'] and not result['imported'] and store.query()[1]==0
 with pytest.raises(InterruptedError):store.import_one(source,cancel=cancel)
 assert source.exists() and not list(store.root.glob('*.tmp')) and store.query()[1]==0
