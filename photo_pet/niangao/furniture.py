"""Interruptible 2D desktop furniture choreography; no 3D collision claim."""
import math,time
from PySide6.QtCore import Qt,QRectF
from PySide6.QtGui import QPainter,QColor,QRegion
from PySide6.QtWidgets import QWidget
from .geometry import nearest_area,clamp_position
from .dialogue import choose
class LightSpot(QWidget):
    def __init__(self):
        super().__init__(None,Qt.WindowType.Tool|Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint|Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground);self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating);self.resize(16,16)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(240,100,110,70));p.drawEllipse(QRectF(0,0,16,16));p.setBrush(QColor('#e86f76'));p.drawEllipse(QRectF(5,5,6,6));p.end()
class FurnitureSession:
    def __init__(self,pet,widget,rng,clock=time.monotonic):
        self.pet=pet;self.widget=widget;self.rng=rng;self.clock=clock;self.started=clock();self.cancelled=False
        self.phase=-1;self.origin=(pet.x(),pet.y());self.item=widget.id;self.reference=(widget.x(),widget.y())
        pet.director.cancel();pet.cursor_mode=False;pet.cursor_target=None
        self.steps=self.plan(widget.id);self.total=sum(v[1] for v in self.steps)
        self.approach=3.;self.start_root=(pet.x()+pet.width()/2,pet.y()+pet.height()-10)
        self.target_root=self.root_for(0)
        pet.perform_action('walk',3,False)
        pet.bubble.speak(choose({'soft_bed':'sleep','bed':'sleep','blanket':'rug','garden_patch':'garden'}.get(widget.id,widget.id)),pet.rect_global(),pet.areas())
    def plan(self,id):
        return {
          'tree':[('climb' if 'climb' in self.pet.art.frames else 'scratch',3),('pounce',1),('climb_top',4)],
          'tunnel':[('stalk',2),('walk',3),('expectant',2)],
          'hammock':[('expectant',3),('bored',3),('sleep',8)],
          'bed':[('knead',3),('sleep',9)],'soft_bed':[('knead',3),('sleep',9)],
          'rug':[('roll',4),('knead',4),('swat',3)],'blanket':[('swat',3),('roll',4),('knead',3)],
          'garden_patch':[('stalk',3),('pounce',2),('bored',5)],
          # Modest discreet squat; keep the photographic asset, do not invent a toileting frame.
          'litter':[('expectant',3),('bored',4),('scratch',2)]}[id]
    def root_for(self,progress):
        w=self.widget;x=w.x()+w.width()/2;y=w.y()+w.width()*.78
        if self.item=='tree':y=w.y()+w.width()*(.75-.56*progress)
        if self.item=='tunnel':x=w.x()+w.width()*(-.2+1.4*progress);y=w.y()+w.width()*.78
        if self.item=='hammock':y=w.y()+w.width()*.60
        return x,y
    def cancel(self):
        self.cancelled=True
        if self.pet.furniture is self:self.pet.furniture=None
        self.pet.behaviour.action('idle',3)
    def tick(self,now):
        pet=self.pet;w=self.widget
        if self.cancelled:return
        if w.uid not in pet.desktop.widgets or w.down or pet.dragging or pet.pressed or pet.work_mode or abs(w.x()-self.reference[0])+abs(w.y()-self.reference[1])>25:self.cancel();return
        elapsed=now-self.started
        if elapsed<self.approach:
            t=min(1,elapsed/self.approach);rx=self.start_root[0]+(self.target_root[0]-self.start_root[0])*t;ry=self.start_root[1]+(self.target_root[1]-self.start_root[1])*t
        else:
            local=elapsed-self.approach
            if local>=self.total:
                pet.life.care('rest' if self.item in ('bed','soft_bed','hammock') else 'litter' if self.item=='litter' else 'play');self.cancel();return
            accumulated=0
            for i,(action,seconds) in enumerate(self.steps):
                if local<accumulated+seconds:
                    if i!=self.phase:self.phase=i;pet.perform_action(action,seconds+1,False)
                    break
                accumulated+=seconds
            progress=min(1,local/(5 if self.item=='tree' else self.total))
            rx,ry=self.root_for(progress)
            if self.item=='tree' and self.phase==1:ry-=math.sin((local-3)*math.pi)*18
            if self.item=='garden_patch':rx+=math.sin(local)*w.width()*.20
            if self.item=='blanket' and self.phase==0:w.body.vx=math.sin(local*3)*70
            if self.item=='tunnel':w.raise_()
        area=nearest_area(rx,ry,pet.areas());x,y=clamp_position(rx-pet.width()/2,ry-pet.height()+10,pet.width(),pet.height(),area)
        pet.float_pos=(x,y);pet.move(round(x),round(y))
