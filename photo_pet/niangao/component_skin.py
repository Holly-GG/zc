"""Reference-derived PNG pieces under native, editable Qt controls and text."""
from functools import lru_cache
from PySide6.QtCore import QRectF
from PySide6.QtGui import QPixmap
from .art import asset_path

PAGE_KEYS=('home','care','backpack','backpack','album','chat','diary','settings','album')

@lru_cache(maxsize=128)
def piece(page,name):
    return QPixmap(str(asset_path(f'ui/layers/components/{page}/{name}.png')))

def ready(page):return asset_path(f'ui/layers/components/{page}/card.png').is_file()

def nine_patch(p,image,box,corner=16,center=True,fractions=(.28,.28)):
    """Keep PNG corners intact while extending only the quiet paper middles."""
    if image.isNull() or box.width()<=0 or box.height()<=0:return
    sw,sh=image.width(),image.height();sx,sy=max(1,sw*fractions[0]),max(1,sh*fractions[1])
    dx=min(corner,box.width()/3);dy=min(corner,box.height()/3)
    xs=(box.left(),box.left()+dx,box.right()-dx,box.right())
    ys=(box.top(),box.top()+dy,box.bottom()-dy,box.bottom())
    us=(0,sx,sw-sx,sw);vs=(0,sy,sh-sy,sh)
    for row in range(3):
        for col in range(3):
            if not center and row==col==1:continue
            p.drawPixmap(QRectF(xs[col],ys[row],xs[col+1]-xs[col],ys[row+1]-ys[row]),image,
                         QRectF(us[col],vs[row],us[col+1]-us[col],vs[row+1]-vs[row]))

def stylesheet(page):
    """Only surfaces use PNG; never render labels as raster artwork."""
    if not ready(page):return ''
    def url(name):return '"'+str(asset_path(f'ui/layers/components/{page}/{name}.png')).replace('\\','/')+'"'
    def image(name):
        # QSS's source slices use native pixels; percentages are unsupported.
        pix=piece(page,name);fx,fy=(.34,.42) if name=='header' else (.28,.28)
        x=max(1,round(pix.width()*fx));y=max(1,round(pix.height()*fy))
        return f'url({url(name)}) {y} {x} {y} {x} stretch stretch'
    # Generated sage surfaces vary by chapter; keep live text legible on them.
    sample=piece(page,'button-active').toImage().pixelColor(piece(page,'button-active').width()//2,piece(page,'button-active').height()//2)
    def luminance(color):
        channels=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in color]
        return sum(v*w for v,w in zip(channels,(.2126,.7152,.0722)))
    bg=luminance((sample.redF(),sample.greenF(),sample.blueF()))
    active_text='#FFFFFF' if 1.05/(bg+.05)>=4.5 else '#000000'
    return f'''
    QFrame#header {{border-image:{image('header')};border-width:10px;background:transparent;}}
    QFrame#paperCard,QFrame#itemCard,QFrame#photoCard,QFrame#chatComposer {{border-image:{image('card')};border-width:8px;background:transparent;}}
    QGroupBox {{border-image:{image('card')};border-width:8px;background:transparent;padding:12px;margin-top:20px;}}
    QPushButton {{border-image:{image('button')};border-width:6px;background:transparent;padding:4px 10px;}}
    QPushButton:hover,QPushButton:pressed,QPushButton#primary {{border-image:{image('button-active')};color:{active_text};}}
    QPushButton:disabled {{border-image:{image('button')};color:#6D7467;}}
    QPushButton:focus,QPushButton#primary:focus,QPushButton#quiet:focus {{border-image:none;border:2px solid #3E7197;background:#EDF0DA;color:#2A472F;}}
    QPushButton#pageLink {{border-image:none;border-width:0px;border-bottom:1px solid #B9AE7A;padding:8px 4px;}}
    QLineEdit,QComboBox,QSpinBox,QDateEdit,QDoubleSpinBox {{border-image:{image('input')};border-width:6px;padding:4px 8px;background:#FCFAF0;}}
    QListWidget#navigation::item:selected {{border-image:{image('navigation')};border-width:5px;color:#FFFFFF;}}
    '''
