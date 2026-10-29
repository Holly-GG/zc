from functools import lru_cache
from PySide6.QtCore import QByteArray,Qt,QRectF
from PySide6.QtGui import QPixmap,QPainter
from PySide6.QtSvg import QSvgRenderer
from ..art import asset_path
@lru_cache(maxsize=128)
def illustrated_item_pixmap(id,size=112):
    """Presentation atlas only; desktop collision masks and empty-bowl states stay intact."""
    cells={'food_bowl':0,'bowl':0,'water_bowl':1,'wand':2,'brush':3,'bed':4,'fish':5,'wet_food':6}
    extra={'water_fountain':0,'ball':1,'wash_basin':2,'scratcher':3,'hammock':4,'litter':5,'tunnel':7}
    atlas=QPixmap(str(asset_path('ui/botanical/objects-extra.webp' if id in extra else 'ui/botanical/objects.webp')))
    if id in extra:cells=extra
    if id not in cells or atlas.isNull():return item_pixmap(id,size)
    cell=cells[id];w,h=atlas.width()//4,atlas.height()//2
    inset=36 if id=='fish' else 0
    margin=14 if id in extra else 0
    image=atlas.copy((cell%4)*w+inset+margin,(cell//4)*h+margin,w-inset-2*margin,h-2*margin)
    return image.scaled(size,size,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)

@lru_cache(maxsize=256)
def item_pixmap(id,size=112,empty=False):
    path=asset_path("items/"+id+".svg")
    data=path.read_bytes()
    if empty and id in ("water_bowl","water_fountain"):
        data=data.replace(b"#a6d8e6",b"#fffaf0").replace(b'stroke="#7dbbcf"',b'stroke="none"')
    if empty and id in ("food_bowl","bowl"):data=data.replace(b"#bd9877",b"#fffaf0")
    renderer=QSvgRenderer(QByteArray(data))
    if not renderer.isValid():raise ValueError("商品图像无效："+id)
    pix=QPixmap(size,size);pix.fill(Qt.GlobalColor.transparent)
    painter=QPainter(pix);painter.setRenderHint(QPainter.RenderHint.Antialiasing);renderer.render(painter,QRectF(0,0,size,size));painter.end()
    return pix
