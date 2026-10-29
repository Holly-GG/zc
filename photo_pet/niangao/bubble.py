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
        self.resize(210,74);self.text=""
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
        from .component_skin import ready,piece,nine_patch
        from .typography import roles
        p.setPen(QColor('#B9AE7A'));p.setBrush(QColor('#FCFAF0'));p.drawRoundedRect(QRectF(1,1,self.width()-2,self.height()-2),8,8)
        if ready('chat'):
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);nine_patch(p,piece('chat','card'),QRectF(self.rect()),10)
        font=QFont(roles()['body']['family']);font.setPixelSize(13);font.setBold(True)
        p.setPen(QColor('#3C582C'));p.setFont(font)
        p.drawText(16,24,"年糕 · NIANGAO")
        font.setBold(False);p.setPen(QColor('#2A472F'));p.setFont(font)
        p.drawText(QRectF(12,29,self.width()-32,self.height()-34),Qt.TextFlag.TextWordWrap,self.text)
        p.end()
