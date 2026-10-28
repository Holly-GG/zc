from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter,QColor,QFont
from PySide6.QtWidgets import QWidget
from .geometry import Rect,bubble_position,nearest_area

PALETTE={"milk":"#EFF6F1","sage":"#899F84","aqua":"#8CCCCA","jade":"#40A387","ink":"#305E63"}
class SpeechBubble(QWidget):
    def __init__(self):
        super().__init__(None,Qt.WindowType.ToolTip|Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint|Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.resize(244,82);self.text=""
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(self.hide)
    def speak(self,text,pet,areas,seconds=3.5):
        self.text=text
        if self.place(pet,areas):self.show();self.raise_();self.timer.start(int(seconds*1000));self.update()
    def place(self,pet,areas):
        area=nearest_area(pet.x,pet.y,areas)
        position=bubble_position(pet,self.width(),self.height(),area)
        if position is None:self.hide();return False
        self.move(round(position[0]),round(position[1]));return True
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QColor(PALETTE["aqua"]));p.setBrush(QColor(PALETTE["milk"]))
        p.drawRoundedRect(QRectF(1,1,self.width()-2,self.height()-2),18,18)
        p.setPen(QColor(PALETTE["jade"]));p.setFont(QFont("Microsoft YaHei",9,QFont.Weight.Bold))
        p.drawText(16,24,"年糕 · NIANGAO")
        p.setPen(QColor(PALETTE["ink"]));p.setFont(QFont("Microsoft YaHei",10))
        p.drawText(QRectF(16,32,self.width()-32,self.height()-38),Qt.TextFlag.TextWordWrap,self.text)
        p.end()
