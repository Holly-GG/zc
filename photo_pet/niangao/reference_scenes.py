"""Illustrated chapter compositions; decoration never owns focus or mouse input."""
from functools import lru_cache
from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath, QLinearGradient, QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QProgressBar
from .art import asset_path

SCENES = ('home', 'care', 'backpack', 'backpack', 'diary', 'chat', 'diary', 'settings', 'album')

@lru_cache(maxsize=12)
def scene_image(name):
    return QPixmap(str(asset_path('ui/botanical/scene-' + name + '.webp')))

def fit_art(p, image, rect):
    if image.isNull(): return
    size = image.size().scaled(rect.size().toSize(), Qt.AspectRatioMode.KeepAspectRatio)
    p.drawPixmap(QRectF(rect.center().x()-size.width()/2, rect.bottom()-size.height(), size.width(), size.height()), image, QRectF(image.rect()))

def cover_art(p, image, rect):
    if image.isNull(): return
    scale = max(rect.width()/image.width(), rect.height()/image.height())
    source = QRectF((image.width()-rect.width()/scale)/2, (image.height()-rect.height()/scale)/2, rect.width()/scale, rect.height()/scale)
    p.drawPixmap(rect, image, source)

def paper_border(p, rect, name, quiet=False):
    """Nine-slice scene margins, preserving rich corners without stretching a page."""
    image = scene_image(name)
    if image.isNull(): return
    sw, sh = image.width(), image.height()
    sx, sy = sw*.18, sh*.20
    corner = min(42 if quiet else 66, rect.width()/3, rect.height()/3)
    edge = 6 if quiet else 12
    x,y,w,h = rect.x(),rect.y(),rect.width(),rect.height()
    for dst, src in (
        (QRectF(x,y,corner,corner),QRectF(0,0,sx,sy)),
        (QRectF(x+w-corner,y,corner,corner),QRectF(sw-sx,0,sx,sy)),
        (QRectF(x,y+h-corner,corner,corner),QRectF(0,sh-sy,sx,sy)),
        (QRectF(x+w-corner,y+h-corner,corner,corner),QRectF(sw-sx,sh-sy,sx,sy)),
        (QRectF(x+corner,y,w-2*corner,edge),QRectF(sx,0,sw-2*sx,sy)),
        (QRectF(x+corner,y+h-edge,w-2*corner,edge),QRectF(sx,sh-sy,sw-2*sx,sy)),
        (QRectF(x,y+corner,edge,h-2*corner),QRectF(0,sy,sx,sh-2*sy)),
        (QRectF(x+w-edge,y+corner,edge,h-2*corner),QRectF(sw-sx,sy,sx,sh-2*sy))):
        if dst.width()>0 and dst.height()>0: p.drawPixmap(dst,image,src)

class ScenePortrait(QWidget):
    """Large dedicated illustration plate, usable beside real forms and instruments."""
    def __init__(self, name='home', pose=None, height=350):
        super().__init__(); self.name=name; self.pose=pose
        if pose is not None and name in ('home','status','settings'):
            candidate=QPixmap(str(asset_path('ui/botanical/candidate-standing.webp')))
            if not candidate.isNull():self.pose=candidate
        self.setMinimumWidth(0); self.setMinimumHeight(height)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAccessibleName('年糕插画预览，待确认')
    def sizeHint(self): return QSize(300,self.minimumHeight())
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHints(QPainter.RenderHint.Antialiasing|QPainter.RenderHint.SmoothPixmapTransform)
        scene=scene_image(self.name)
        # Left-side portrait scenes are intentionally cropped to their illustrated half.
        if not scene.isNull():
            source=QRectF(0,0,scene.width()*(.48 if self.name in ('home','status','settings') else 1),scene.height())
            p.drawPixmap(QRectF(self.rect()),scene,source)
        if self.pose is not None:
            fit_art(p,self.pose,QRectF(12,30,self.width()-24,self.height()-58))
        p.setPen(QColor('#66745C'));f=p.font();f.setPixelSize(10);p.setFont(f)
        p.fillRect(QRectF(8,self.height()-27,self.width()-16,21),QColor(250,247,233,235))
        p.drawText(QRectF(8,self.height()-27,self.width()-16,21),Qt.AlignmentFlag.AlignCenter,'年糕专属插画 · 待确认');p.end()

class SpecimenStrip(QWidget):
    def __init__(self):
        super().__init__();self.setMinimumWidth(0);self.setFixedHeight(116)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAccessibleName('装饰：迷迭香、鼠尾草与蕨叶植物标本')
    def paintEvent(self,event):
        from .journal import branch
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        names=('迷迭香 / Rosemary','鼠尾草 / Sage','蕨叶 / Fern')
        width=(self.width()-16)/3
        for i,name in enumerate(names):
            r=QRectF(i*(width+8),2,width,110)
            p.setPen(QPen(QColor('#B9AE7A'),.8));p.setBrush(QColor('#FCF8E9'));p.drawRoundedRect(r,4,4)
            branch(p,r.center().x()-5,83,68,-12,'#687F48',i==2)
            p.fillRect(QRectF(r.center().x()-16,3,32,8),QColor(180,211,236,130))
            p.setPen(QColor('#3C582C'));f=p.font();f.setPixelSize(10);p.setFont(f)
            p.drawText(QRectF(r.x()+3,88,width-6,20),Qt.AlignmentFlag.AlignCenter,name)
        p.end()

class StatusChapter(QWidget):
    """Reference R05 rendered from existing live stats/events, without a new data model."""
    def __init__(self, engine):
        super().__init__();self.engine=engine;self.setMinimumWidth(0)
        from .journal import portrait
        from .journal_components import PaperCard, ResponsiveColumns, StateRing, CardGrid
        from .life.engine import STAT_NAMES
        from .theme import STATE_COLORS
        outer=QVBoxLayout(self);outer.setContentsMargins(0,0,0,0);outer.setSpacing(12)
        identity=PaperCard();identity.body.setContentsMargins(8,8,8,8)
        identity.body.addWidget(ScenePortrait('status',portrait(7),390))
        self.profile=QLabel();self.profile.setWordWrap(True);identity.body.addWidget(self.profile)
        right=QWidget();column=QVBoxLayout(right);column.setContentsMargins(0,0,0,0);column.setSpacing(12);column.setAlignment(Qt.AlignmentFlag.AlignTop)
        heading=QLabel('宠物状态  ·  Pet Status');heading.setObjectName('sectionTitle');column.addWidget(heading)
        hint=QLabel('和年糕一起，收集一天的温柔时光。');hint.setObjectName('sub');column.addWidget(hint)
        self.rings={};cards=CardGrid(112)
        for key,icon in (('mood','affection'),('satiety','food_bowl'),('energy','ball')):
            card=PaperCard();ring=StateRing(STAT_NAMES[key],STATE_COLORS[key],icon);card.body.addWidget(ring);self.rings[key]=ring;cards.cards.append(card)
        cards.set_cards(cards.cards);column.addWidget(cards)
        self.levels={}
        for key in ('cleanliness','health'):
            card=PaperCard(STAT_NAMES[key]);bar=QProgressBar();bar.setRange(0,100);bar.setFormat('%v%');card.body.addWidget(bar);column.addWidget(card);self.levels[key]=bar
        note=PaperCard('今日变化 / Today’s Record');self.events=QLabel();self.events.setTextFormat(Qt.TextFormat.PlainText);self.events.setWordWrap(True);note.body.addWidget(self.events);column.addWidget(note)
        outer.addWidget(ResponsiveColumns(identity,right,(4,6),680));self.refresh()
    def refresh(self):
        from .life.profile import sanitize_profile
        e=self.engine;p=sanitize_profile(e.data['profile'])
        self.profile.setText('年糕 NIANGAO · 布偶猫\n生日 '+e.data['birth_date']+'\n性格：'+(p['personality'] or '尚未填写'))
        for key,ring in self.rings.items():ring.setValue(round(e.data['stats'][key]))
        for key,bar in self.levels.items():bar.setValue(round(e.data['stats'][key]))
        events=[v for v in e.data['events'] if v['day']==e.today().isoformat()][-6:]
        self.events.setText('\n'.join(v['at'][11:16]+'  '+v['text'] for v in reversed(events)) if events else '还没有陪伴记录，和年糕度过一会儿吧。')
