"""Presentation-only botanical journal surfaces. No input handlers or application state."""
import random
from PySide6.QtCore import Qt,QRectF,QPointF
from PySide6.QtGui import QColor,QPainter,QPainterPath,QPen,QLinearGradient,QPixmap
from PySide6.QtWidgets import QWidget,QFrame,QLabel,QHBoxLayout,QVBoxLayout

# Each chapter varies its paper, dominant wash, ornament and density.
CHAPTERS=(
 dict(key='overview',number='I',name='THE GARDEN COMPANION',paper='#F4F0DC',wash='#92AB76',accent='#3C582C',motif='arch',density=1.0),
 dict(key='care',number='II',name='HERBARIUM · DAILY CARE',paper='#EFF2DE',wash='#B4D3EC',accent='#3C582C',motif='herb',density=.65),
 dict(key='shop',number='III',name='THE LITTLE APOTHECARY',paper='#F3EDDA',wash='#839D45',accent='#2A472F',motif='flower',density=.75),
 dict(key='backpack',number='IV',name='COLLECTED TREASURES',paper='#EDF1E2',wash='#92AB76',accent='#3C582C',motif='fern',density=.6),
 dict(key='focus',number='V',name='A QUIET HOUR',paper='#EDF3ED',wash='#B4D3EC',accent='#2A472F',motif='coast',density=.4),
 dict(key='chat',number='VI',name='LETTERS TO NIANGAO',paper='#F8F7EF',wash='#B4D3EC',accent='#2A472F',motif='letter',density=0),
 dict(key='diary',number='VII',name='FIELD NOTES · MEMORIES',paper='#F3EFDF',wash='#92AB76',accent='#3C582C',motif='manuscript',density=.55),
 dict(key='settings',number='VIII',name='PORTRAIT & PARTICULARS',paper='#EEF0DF',wash='#839D45',accent='#2A472F',motif='seed',density=.35),
)

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
        super().__init__();self.chapter=CHAPTERS[index];self.setObjectName('journalPage');self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,False)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);c=self.chapter;p.fillRect(self.rect(),QColor(c['paper']))
        if c['density']:
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
        p.end()

class ChapterHeading(QFrame):
    def __init__(self,index,title,subtitle,pixmap=None):
        super().__init__();self.index=index;self.chapter=CHAPTERS[index];self.setObjectName('chapterHeading');self.setMinimumHeight(156 if index==0 else 125 if index!=5 else 96)
        row=QHBoxLayout(self);row.setContentsMargins(18,18,14,17);text=QVBoxLayout();text.setSpacing(5);row.addLayout(text,1)
        eyebrow=QLabel(self.chapter['number']+'  /  '+self.chapter['name']);eyebrow.setObjectName('eyebrow');text.addWidget(eyebrow)
        label=QLabel(title);label.setWordWrap(True);label.setObjectName('hero');text.addWidget(label)
        if subtitle:
            label=QLabel(subtitle);label.setWordWrap(True);label.setObjectName('sub');text.addWidget(label)
        if pixmap is not None and not pixmap.isNull() and index!=5:
            art=QLabel();art.setObjectName('chapterPortrait');art.setFixedSize(98 if index==0 else 82,116 if index==0 else 94);art.setAlignment(Qt.AlignmentFlag.AlignCenter);art.setPixmap(pixmap.scaled(art.size(),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation));row.addWidget(art)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);c=self.chapter;w,h=self.width(),self.height()
        p.fillRect(QRectF(2,4,w-4,h-5),QColor(42,71,47,12));p.fillRect(QRectF(0,0,w-3,h-5),QColor('#FCFAF0'))
        if self.index==5:
            p.setPen(QPen(QColor('#B4D3EC'),1));p.drawLine(18,h-7,w-18,h-7);p.end();return
        # Watercolour wash stays in portrait margin; body text retains a solid paper base.
        g=QLinearGradient(w-150,0,w,90);g.setColorAt(0,QColor(255,255,255,0));q=QColor(c['wash']);q.setAlpha(110);g.setColorAt(1,q);p.fillRect(QRectF(w-155,0,152,h-5),g)
        p.setPen(QPen(QColor('#A1AD7C'),.7));p.drawRect(QRectF(5,5,w-14,h-16))
        if c['motif']=='arch':
            arch(p,QRectF(w-115,8,100,h-22));branch(p,w-133,h-12,70,-22);flower(p,w-128,30,.7)
        elif c['motif']=='flower':
            for x,y in [(w-109,26),(w-17,h-25)]:flower(p,x,y,.8);branch(p,x,y+40,44,16)
        elif c['motif']=='coast':
            p.setPen(QPen(QColor('#77AAD7'),.7))
            for y in range(h-22,h-8,5):
                path=QPainterPath(QPointF(w-140,y));path.cubicTo(w-100,y-7,w-45,y+6,w-12,y-2);p.drawPath(path)
        elif c['motif']=='manuscript':
            p.setPen(QPen(QColor('#CDD1AF'),.6))
            for y in range(22,h-15,13):p.drawLine(w-128,y,w-12,y)
            branch(p,w-20,h-13,85,-20)
        else:branch(p,w-13,h-14,85,-18,c['accent'],c['motif']=='fern')
        # Semi-transparent washi, torn lower edge, and a tiny botanical wax seal.
        p.fillRect(QRectF(24,0,57,7),QColor(146,171,118,90))
        p.setPen(QPen(QColor('#3C582C'),.6));p.setBrush(QColor('#92AB76'));p.drawEllipse(QRectF(w-27,h-23,15,15));p.setPen(QPen(QColor('#E8E9C0'),.6));p.drawLine(QPointF(w-23,h-12),QPointF(w-17,h-20))
        p.setPen(QPen(QColor('#B6BE93'),.6));path=QPainterPath(QPointF(7,h-7))
        for x in range(7,w-7,7):path.lineTo(x,h-7+(x%3))
        p.drawPath(path)
        p.end()

class JournalSidebar(QFrame):
    def paintEvent(self,event):
        super().paintEvent(event);p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.setOpacity(.6);branch(p,26,self.height()-12,57,-16,'#3C582C');branch(p,self.width()-24,self.height()-12,49,23,'#3C582C');flower(p,self.width()/2,self.height()-25,.55);p.end()
