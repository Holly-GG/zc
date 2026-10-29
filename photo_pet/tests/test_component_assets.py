"""Component surfaces remain separate from live content and retain real alpha."""
import hashlib,json
from PySide6.QtGui import QImage

def test_reference_component_pack_is_complete_and_transparent():
 from niangao.art import asset_path
 root=asset_path('ui/layers/components');rows=json.loads((root/'manifest.json').read_text())['components']
 assert len(rows)==96
 for page in ('home','chat','care','backpack','diary','settings','album','status'):
  found={r['component']:r for r in rows if r['page']==page}
  assert set(found)=={'paper','frame','header','card','button','button-active','input','navigation','corner-top','corner-bottom','character','objects'}
  frame=QImage(str(root/found['frame']['file']))
  assert frame.pixelColor(frame.width()//2,frame.height()//2).alpha()<5
  assert found['character']['status']=='candidate-not-enabled'
 for row in rows:
  path=root/row['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
  image=QImage(str(path));assert not image.isNull() and image.width()==row['width']

def test_every_product_has_an_independent_display_png():
 from niangao.art import asset_path
 from niangao.life.catalog import BY_ID
 root=asset_path('ui/layers/products');rows=json.loads((root/'manifest.json').read_text())['components']
 assert {row['component'] for row in rows}==set(BY_ID)
 for row in rows:
  path=root/row['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
  image=QImage(str(path));assert not image.isNull() and image.hasAlphaChannel()
