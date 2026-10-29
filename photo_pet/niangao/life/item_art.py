from functools import lru_cache
from PySide6.QtCore import QByteArray,Qt,QRectF
from PySide6.QtGui import QPixmap,QPainter
from PySide6.QtSvg import QSvgRenderer
from ..art import asset_path
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
