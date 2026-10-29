"""Presentation-only botanical journal surfaces. No input handlers or application state."""
import random
from functools import lru_cache
from .art import asset_path
from PySide6.QtCore import Qt,QRectF,QPointF
from PySide6.QtGui import QColor,QPainter,QPainterPath,QPen,QLinearGradient,QPixmap,QIcon
from PySide6.QtWidgets import QWidget,QFrame,QLabel,QHBoxLayout,QVBoxLayout,QListWidget

# Each chapter varies its paper, dominant wash, ornament and density.
CHAPTERS=(
 dict(key='overview',number='I',name='THE GARDEN COMPANION',paper='#F4F0DC',wash='#A4CAB8',accent='#3C582C',motif='arch',density=1.0),
 dict(key='care',number='II',name='HERBARIUM · DAILY CARE',paper='#EFF2DE',wash='#B4D3EC',accent='#3C582C',motif='herb',density=.65),
 dict(key='shop',number='III',name='THE LITTLE APOTHECARY',paper='#F3EDDA',wash='#839D45',accent='#2A472F',motif='flower',density=.75),
 dict(key='backpack',number='IV',name='COLLECTED TREASURES',paper='#EDF1E2',wash='#92AB76',accent='#3C582C',motif='fern',density=.6),
 dict(key='focus',number='V',name='A QUIET HOUR',paper='#EDF3ED',wash='#B4D3EC',accent='#2A472F',motif='coast',density=.4),
 dict(key='chat',number='VI',name='LETTERS TO NIANGAO',paper='#F8F7EF',wash='#B4D3EC',accent='#2A472F',motif='letter',density=0),
 dict(key='diary',number='VII',name='FIELD NOTES · MEMORIES',paper='#F3EFDF',wash='#92AB76',accent='#3C582C',motif='manuscript',density=.55),
 dict(key='settings',number='VIII',name='PORTRAIT & PARTICULARS',paper='#EEF0DF',wash='#839D45',accent='#2A472F',motif='seed',density=.35),
 dict(key='album',number='IX',name='COLLECTED DAYS',paper='#F0F4ED',wash='#B4D3EC',accent='#3E7197',motif='coast',density=.3),
)


@lru_cache(maxsize=20)
def decorative_asset(name):
    from .layers import layer
    return layer(name)

def portrait(index):
    if index==8:return QPixmap()
    atlas=decorative_asset('poses')
    if atlas.isNull():return QPixmap()
    # Read-only sprite view: illustrations remain separate from interactive controls.
    cell={0:1,1:0,2:0,3:2,4:3,5:3,6:1,7:1}[index]
    w,h=atlas.width()//2,atlas.height()//2
    inset=60 if cell==1 else 0
    return atlas.copy((cell%2)*w+inset,(cell//2)*h,w-inset,h)

def floral_frame(p,rect,quiet=False):
    image=decorative_asset('border')
    if image.isNull():return
    p.save();p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    # Nine-slice an ornament, never a screenshot: corners keep their proportions,
    # long notebook pages do not stretch flowers into tall vertical bands.
    sw,sh=image.width(),image.height();sx,sy=310,230
    corner=min(34 if quiet else 61,rect.width()/2,rect.height()/2);edge=min(9 if quiet else 17,corner/2)
    x,y,w,h=rect.x(),rect.y(),rect.width(),rect.height()
    cells=[(QRectF(x,y,corner,corner),QRectF(0,0,sx,sy)),
      (QRectF(x+w-corner,y,corner,corner),QRectF(sw-sx,0,sx,sy)),
      (QRectF(x,y+h-corner,corner,corner),QRectF(0,sh-sy,sx,sy)),
      (QRectF(x+w-corner,y+h-corner,corner,corner),QRectF(sw-sx,sh-sy,sx,sy)),
      (QRectF(x+corner,y,w-2*corner,edge),QRectF(sx,0,sw-2*sx,sy)),
      (QRectF(x+corner,y+h-edge,w-2*corner,edge),QRectF(sx,sh-sy,sw-2*sx,sy)),
      (QRectF(x,y+corner,edge,h-2*corner),QRectF(0,sy,sx,sh-2*sy)),
      (QRectF(x+w-edge,y+corner,edge,h-2*corner),QRectF(sw-sx,sy,sx,sh-2*sy))]
    p.setOpacity(.55 if quiet else .95)
    for destination,source in cells:
        if destination.width()>0 and destination.height()>0:p.drawPixmap(destination,image,source)
    p.restore()

class HeroIllustration(QLabel):
    def __init__(self):
        super().__init__();self.setMinimumWidth(165);self.setMinimumHeight(440)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);image=decorative_asset('candidate-standing')
        scene=decorative_asset('moon-window')
        if not scene.isNull():
            from .reference_scenes import cover_art
            p.setOpacity(.85);cover_art(p,scene,QRectF(self.rect()));p.setOpacity(1)
        # Keep the full artwork and natural anatomy; no stretched character images.
        if not image.isNull():
            size=image.size();size.scale(self.size(),Qt.AspectRatioMode.KeepAspectRatio);r=QRectF((self.width()-size.width())/2,(self.height()-size.height())/2,size.width(),size.height());p.drawPixmap(r,image,QRectF(image.rect()))
        note=QRectF(8,self.height()-26,self.width()-16,22)
        p.fillRect(note,QColor(252,250,240,245));p.setPen(QColor('#2A472F'));font=p.font();font.setPixelSize(12);p.setFont(font);p.drawText(note,Qt.AlignmentFlag.AlignCenter,'年糕专属插画 · 待确认');p.end()

def branch(p,x,y,size=70,angle=-25,color='#839D45',fern=False):
    p.save();p.translate(x,y);p.rotate(angle)
    p.setPen(QPen(QColor(color),.8));path=QPainterPath(QPointF(0,0));path.cubicTo(-5,-size*.3,6,-size*.7,0,-size);p.drawPath(path)
    for i in range(1,7):
        yy=-size*i/7;span=size*(.18 if fern else .13)*(1-i/9)
        for sign in (-1,1):
            leaf=QPainterPath(QPointF(0,yy));leaf.cubicTo(sign*span,-size*i/7-5,sign*span*1.6,yy-13,sign*span*.6,yy-15);leaf.quadTo(sign*2,yy-9,0,yy)
            fill=QColor(color);fill.setAlpha(50 if fern else 75);p.fillPath(leaf,fill);p.drawPath(leaf)
    p.restore()

def flower(p,x,y,scale=1):
    p.save();p.translate(x,y);p.scale(scale,scale);p.setPen(QPen(QColor('#839D45'),.8))
    for a in range(0,360,72):
        p.save();p.rotate(a);p.setBrush(QColor('#E8E9C0'));p.drawEllipse(QRectF(-3,-13,6,12));p.restore()
    p.setBrush(QColor('#77AAD7'));p.drawEllipse(QRectF(-2,-2,4,4));p.restore()

def arch(p,r,color='#839D45'):
    x,y,w,h=r.x(),r.y(),r.width(),r.height();path=QPainterPath(QPointF(x,y+h));path.lineTo(x,y+h*.38);path.cubicTo(x,y+h*.16,x+w*.30,y+h*.05,x+w*.5,y);path.cubicTo(x+w*.7,y+h*.05,x+w,y+h*.16,x+w,y+h*.38);path.lineTo(x+w,y+h)
    p.setPen(QPen(QColor(color),1));p.drawPath(path)
    p.setPen(QPen(QColor(color),.5));p.drawLine(QPointF(x+w*.5,y+10),QPointF(x+w*.5,y+h));p.drawLine(QPointF(x+3,y+h*.6),QPointF(x+w-3,y+h*.6))

class PaperPage(QWidget):
    def __init__(self,index=0):
        super().__init__();self.index=index;self.chapter=CHAPTERS[index];self.setObjectName('journalPage');self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,False)
    def paintEvent(self,event):
        from .component_skin import ready,piece,nine_patch,PAGE_KEYS
        key=PAGE_KEYS[self.index]
        if ready(key):
            p=QPainter(self);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            p.fillRect(self.rect(),QColor(self.chapter['paper']))
            p.save();p.setOpacity(.20);p.drawTiledPixmap(self.rect(),piece(key,'paper'));p.restore()
            nine_patch(p,piece(key,'frame'),QRectF(self.rect()).adjusted(1,1,-1,-1),18,center=False)
            p.end();return
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);c=self.chapter;p.fillRect(self.rect(),QColor(c['paper']))
        if c['density']:
            p.save();p.setOpacity(.14);p.drawTiledPixmap(self.rect(),decorative_asset('paper'));p.restore()
            # Deterministic, low-contrast paper fibres; decoration is painted below widgets.
            rng=random.Random(1921)
            p.setPen(QPen(QColor(70,82,43,12),.6))
            for _ in range(min(5000,self.width()*self.height()//130)):
                x=rng.randrange(max(1,self.width()));y=rng.randrange(max(1,self.height()));p.drawLine(QPointF(x,y),QPointF(x+rng.randrange(1,4),y+.4))
            p.setPen(QPen(QColor('#CBD0A8'),.7));p.drawLine(3,18,3,self.height()-16);p.drawLine(self.width()-4,18,self.width()-4,self.height()-16)
            # Edge-only stems never sit behind text, fields, or product imagery.
            p.setOpacity(.4*c['density']);w=self.width();h=self.height();motif=c['motif']
            if motif=='coast':
                p.setPen(QPen(QColor('#77AAD7'),.7))
                for y in range(h-35,h-8,7):p.drawLine(12,y,w-12,y)
            elif motif=='manuscript':
                p.setPen(QPen(QColor('#839D45'),.7))
                for y in range(170,h-15,28):p.drawLine(4,y,11,y)
                branch(p,w-7,h-12,100,-9,c['accent'])
            elif motif=='flower':
                for y in range(175,min(h-10,440),90):flower(p,w-8,y,.65)
                branch(p,7,h-14,70,8,c['accent'])
            elif motif=='seed':
                p.setPen(QPen(QColor('#839D45'),.6))
                for y in range(175,min(h-10,390),30):p.drawEllipse(QRectF(w-9,y,5,9))
            elif motif=='herb':
                branch(p,7,260,90,4,c['accent']);branch(p,w-7,190,65,-8,'#77AAD7')
            else:
                branch(p,w-8,180,100,0,c['accent'],motif=='fern');branch(p,7,h-22,80,8,c['accent'],motif=='fern')
            p.setOpacity(1)
        from .reference_scenes import paper_border,SCENES
        paper_border(p,QRectF(0,0,self.width(),self.height()),SCENES[self.index],self.index==5)
        p.end()

class ChapterHeading(QFrame):
    def __init__(self,index,title,subtitle,pixmap=None):
        super().__init__();self.index=index;self.chapter=CHAPTERS[index];self.setObjectName('chapterHeading');self.setMinimumWidth(0);self.wrapped_labels=[]
        row=QHBoxLayout(self);row.setContentsMargins(16,16,16,32 if index not in (4,5,7) else 16);row.setSpacing(16);text=QVBoxLayout();text.setSpacing(8);text.setAlignment(Qt.AlignmentFlag.AlignVCenter);row.addLayout(text,3)
        eyebrow=QLabel(self.chapter['number']+'  /  NIANGAO JOURNAL');eyebrow.setObjectName('eyebrow');text.addWidget(eyebrow)
        label=QLabel(title);label.setWordWrap(True);label.setMinimumWidth(0);label.setObjectName('hero');text.addWidget(label);self.wrapped_labels.append(label)
        english=('Daily Life','Care & Play','The Little Shop','Forest Collection','Quiet Hours','Chat with Niangao','Magic Diary','Profile & Settings','Collected Days')[index]
        script=QLabel(english);script.setObjectName('scriptTitle');text.addWidget(script)
        if subtitle:
            label=QLabel(subtitle);label.setWordWrap(True);label.setMinimumWidth(0);label.setObjectName('sub');text.addWidget(label);self.wrapped_labels.append(label)
        from .reference_scenes import ChapterArtwork
        self.art_panel=ChapterArtwork(index)
        if index in (0,5):self.art_panel.hide()
        row.addWidget(self.art_panel)
    def minimumSizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(0,self.layout().minimumSize().height())
    def resizeEvent(self,event):
        # Readable labels retain their pixel size; decoration yields first.
        self.art_panel.setVisible(self.index not in (0,5) and self.width()>=(420 if self.index in (4,7) else 480))
        margins=self.layout().contentsMargins()
        width=max(1,self.width()-margins.left()-margins.right()-(self.art_panel.width()+self.layout().spacing() if not self.art_panel.isHidden() else 0))
        for label in self.wrapped_labels:
            label.setMinimumHeight(max(label.fontMetrics().height(),label.heightForWidth(width)))
        self.setMinimumHeight(self.layout().minimumSize().height());self.updateGeometry()
        super().resizeEvent(event)
    def paintEvent(self,event):
        from .layers import layer
        from .component_skin import ready,piece,nine_patch,PAGE_KEYS
        p=QPainter(self);p.setRenderHints(QPainter.RenderHint.Antialiasing|QPainter.RenderHint.SmoothPixmapTransform)
        key=PAGE_KEYS[self.index]
        if ready(key):
            p.fillRect(self.rect(),QColor('#FCFAF0'))
            p.save();p.setOpacity(.15);p.drawTiledPixmap(self.rect(),piece(key,'paper'));p.restore()
            nine_patch(p,piece(key,'header'),QRectF(self.rect()),20,center=False,fractions=(.34,.42))
            p.end();return
        paper=QRectF(self.rect()).adjusted(1,1,-1,-1)
        p.setPen(QPen(QColor('#B9AE7A'),1));p.setBrush(QColor('#FCFAF0'));p.drawRoundedRect(paper,8,8)
        p.save();p.setOpacity(.08);p.drawTiledPixmap(self.rect(),layer('paper'));p.restore()
        # Separate PNG ornament stays beneath an opaque writing area.
        if self.index not in (4,5,7) and self.art_panel.isHidden():
            image=layer('header-ornament')
            if not image.isNull():
                size=image.size().scaled(72,24,Qt.AspectRatioMode.KeepAspectRatio)
                p.drawPixmap(QRectF(self.width()-size.width()-12,self.height()-size.height()-4,size.width(),size.height()),image,QRectF(image.rect()))
        p.end()

class JournalSidebar(QFrame):
    def paintEvent(self,event):
        super().paintEvent(event)
        nav=self.findChild(QListWidget,'navigation')
        if nav is None or nav.count()==0:return
        last=nav.visualItemRect(nav.item(nav.count()-1)).bottom()+nav.y()
        if self.height()-last<105:return
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);image=decorative_asset('forest-collection');p.drawPixmap(QRectF(0,self.height()-100,self.width(),95),image,QRectF(image.rect()));p.end()


def navigation_icon(index):
    pixmap=QPixmap(24,24);pixmap.fill(Qt.GlobalColor.transparent);p=QPainter(pixmap);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.setPen(QPen(QColor('#3C582C'),1.7,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin));p.setBrush(Qt.BrushStyle.NoBrush)
    if index==0:
        path=QPainterPath(QPointF(3,11));path.lineTo(12,3);path.lineTo(21,11);path.moveTo(5,10);path.lineTo(5,21);path.lineTo(19,21);path.lineTo(19,10);path.moveTo(10,21);path.lineTo(10,14);path.lineTo(14,14);path.lineTo(14,21);p.drawPath(path)
    elif index==1:
        p.drawEllipse(QRectF(4,9,6,8));p.drawEllipse(QRectF(14,9,6,8));p.drawLine(7,3,7,6);p.drawLine(17,3,17,6);p.drawLine(12,6,12,9);p.drawLine(9,19,15,19)
    elif index in (2,3):
        p.drawRoundedRect(QRectF(4,8,16,13),2,2);p.drawArc(QRectF(8,2,8,12),0,180*16);p.drawLine(5,13,19,13)
    elif index==4:
        p.drawEllipse(QRectF(3,3,18,18));p.drawLine(12,6,12,12);p.drawLine(12,12,17,15)
    elif index==5:
        p.drawRoundedRect(QRectF(3,4,18,14),4,4);p.drawLine(7,18,5,22)
        for x in (7,12,17):p.drawEllipse(QRectF(x-1,10,2,2))
    elif index==6:
        p.drawRoundedRect(QRectF(5,3,15,19),2,2);p.drawLine(8,3,8,22);p.drawLine(11,8,17,8);p.drawLine(11,12,17,12)
    elif index==7:
        p.drawEllipse(QRectF(4,4,16,16));p.drawEllipse(QRectF(9,9,6,6))
        for x,y,xx,yy in ((12,1,12,4),(12,20,12,23),(1,12,4,12),(20,12,23,12)):p.drawLine(x,y,xx,yy)
    else:
        p.drawRoundedRect(QRectF(3,4,18,16),2,2);p.drawEllipse(QRectF(6,7,4,4));path=QPainterPath(QPointF(4,18));path.lineTo(11,11);path.lineTo(16,16);path.lineTo(20,12);p.drawPath(path)
    p.end();return QIcon(pixmap)
