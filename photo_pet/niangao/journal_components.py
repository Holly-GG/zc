"""Reusable presentation widgets: responsive layouts, paper cards and state rings."""
from PySide6.QtCore import Qt,QRectF,QSize,QPointF
from PySide6.QtGui import QColor,QPainter,QPen,QFont,QIcon,QPainterPath
from PySide6.QtWidgets import QWidget,QFrame,QBoxLayout,QVBoxLayout,QGridLayout,QLabel,QPushButton,QSizePolicy
from .life.item_art import item_pixmap

class FeedbackLabel(QLabel):
    def __init__(self,text=''):
        super().__init__(text);self.setObjectName('sub');self.setWordWrap(True);self.setTextFormat(Qt.TextFormat.PlainText)
    def show_message(self,text,severity='info'):
        super().setText(text);self.setProperty('severity',severity);self.style().unpolish(self);self.style().polish(self)
    def setText(self,text):self.show_message(text)

class PaperCard(QFrame):
    def __init__(self,title='',subtitle='',parent=None):
        super().__init__(parent);self.setObjectName('paperCard');self.setMinimumWidth(0)
        self.body=QVBoxLayout(self);self.body.setContentsMargins(14,14,14,14);self.body.setSpacing(10);self.body.setAlignment(Qt.AlignmentFlag.AlignTop)
        if title:
            label=QLabel(title);label.setObjectName('sectionTitle');label.setWordWrap(True);self.body.addWidget(label)
        if subtitle:
            label=QLabel(subtitle);label.setObjectName('sub');label.setWordWrap(True);self.body.addWidget(label)

class ResponsiveColumns(QWidget):
    def __init__(self,first,second,weights=(1,1),threshold=580,hide_first=False):
        super().__init__();self.threshold=threshold;self.first=first;self.hide_first=hide_first;self.setMinimumWidth(0)
        self.row=QBoxLayout(QBoxLayout.Direction.LeftToRight,self);self.row.setContentsMargins(0,0,0,0);self.row.setSpacing(14)
        for widget,weight in zip((first,second),weights):
            widget.setMinimumWidth(0);widget.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred);self.row.addWidget(widget,weight)
    def minimumSizeHint(self):
        # The horizontal child minimum must not force the scroll page wider before
        # resizeEvent gets a chance to switch the columns into a vertical stack.
        return QSize(0,self.row.minimumSize().height())
    def resizeEvent(self,event):
        if self.hide_first:self.first.setVisible(self.width()>=self.threshold)
        self.row.setDirection(QBoxLayout.Direction.LeftToRight if self.hide_first or self.width()>=self.threshold else QBoxLayout.Direction.TopToBottom)
        super().resizeEvent(event)

class CardGrid(QWidget):
    def __init__(self,minimum=155):
        super().__init__();self.minimum=minimum;self.cards=[];self.columns=0;self.setMinimumWidth(0)
        self.grid=QGridLayout(self);self.grid.setContentsMargins(0,0,0,0);self.grid.setSpacing(12)
    def set_cards(self,cards):
        self.cards=list(cards);self.columns=0;self.reflow()
    def reflow(self):
        columns=max(1,min(3,(self.width()+12)//(self.minimum+12)))
        if columns==self.columns:return
        self.columns=columns
        while self.grid.count():self.grid.takeAt(0)
        for i,card in enumerate(self.cards):self.grid.addWidget(card,i//columns,i%columns)
        for col in range(3):self.grid.setColumnStretch(col,1 if col<columns else 0)
    def resizeEvent(self,event):self.reflow();super().resizeEvent(event)

class StateRing(QWidget):
    def __init__(self,label,color,icon_id):
        super().__init__();self.label=label;self.color=color;self.icon=item_pixmap(icon_id,28)
        self._value=0;self.setMinimumWidth(92);self.setFixedHeight(118);self.setAccessibleName(label)
    def value(self):return self._value
    def setValue(self,value):
        self._value=max(0,min(100,int(value)));self.setAccessibleDescription(f'{self.label} {self._value}%');self.update()
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        diameter=min(72,self.width()-18);x=(self.width()-diameter)/2;ring=QRectF(x,8,diameter,diameter)
        p.setPen(QPen(QColor('#E0E5CF'),6));p.drawEllipse(ring)
        p.setPen(QPen(QColor(self.color),6,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap));p.drawArc(ring,90*16,-round(self.value()*3.6*16))
        p.setPen(QPen(QColor('#839D45'),.6))
        for sign in (-1,1):
            path=QPainterPath(QPointF(self.width()/2+sign*(diameter/2+4),44));path.quadTo(self.width()/2+sign*(diameter/2+10),60,self.width()/2+sign*(diameter/2-4),76);p.drawPath(path)
        p.drawPixmap(round(self.width()/2-12),20,24,24,self.icon)
        p.setPen(QColor('#2A472F'));font=QFont(self.font());font.setPixelSize(17);font.setBold(True);p.setFont(font)
        p.drawText(QRectF(x,45,diameter,26),Qt.AlignmentFlag.AlignCenter,f'{self.value()}%')
        font.setPixelSize(13);p.setFont(font);p.drawText(QRectF(0,86,self.width(),23),Qt.AlignmentFlag.AlignCenter,self.label);p.end()

class CareButton(QPushButton):
    def __init__(self,text,icon_id):
        super().__init__(text);self.icon_id=icon_id;self.setObjectName('careAction');self.setMinimumHeight(100)
        self.setIcon(QIcon(item_pixmap(icon_id,52)));self.setAccessibleName(text)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        fill='#E8E9C0' if self.underMouse() else '#FCF8E9'
        if self.isDown():fill='#DCE3C5'
        if not self.isEnabled():fill='#ECECE2'
        p.setBrush(QColor(fill));p.setPen(QPen(QColor('#3E7197' if self.hasFocus() else '#B9AE7A'),2 if self.hasFocus() else 1));p.drawRoundedRect(QRectF(1,1,self.width()-2,self.height()-2),7,7)
        p.setPen(QPen(QColor('#E3D9B7'),.7));p.setBrush(Qt.BrushStyle.NoBrush);p.drawRoundedRect(QRectF(5,5,self.width()-10,self.height()-10),5,5)
        image=item_pixmap(self.icon_id,52);p.drawPixmap(round(self.width()/2-26),9,image)
        p.setPen(QColor('#2A472F' if self.isEnabled() else '#6D7467'));p.setFont(self.font());p.drawText(QRectF(6,64,self.width()-12,27),Qt.AlignmentFlag.AlignCenter,self.text());p.end()
