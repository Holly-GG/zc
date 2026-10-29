"""Settings choices change on explicit selection, never by scrolling past them."""
from PySide6.QtCore import Qt,QSize,QRect
from PySide6.QtGui import QPainter,QPalette
from PySide6.QtWidgets import QComboBox,QSpinBox,QSizePolicy,QCheckBox,QStyle,QStyleOptionButton
class ClickSelectComboBox(QComboBox):
    def __init__(self,parent=None):
        super().__init__(parent);self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon);self.setMinimumContentsLength(12)
        self.setMinimumWidth(0);self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred)
        self.currentTextChanged.connect(self.setToolTip)
    def wheelEvent(self,event):event.ignore()
    def keyPressEvent(self,event):
        if event.key()==Qt.Key.Key_Escape:self.hidePopup();event.accept()
        else:event.ignore()

class ExplicitSpinBox(QSpinBox):
    def wheelEvent(self,event):event.ignore()

class WrappingCheckBox(QCheckBox):
    """Keep complete consent text readable without widening a settings page."""
    def __init__(self,text='',parent=None):
        super().__init__(text,parent)
        policy=QSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred);policy.setHeightForWidth(True);self.setSizePolicy(policy)
    def heightForWidth(self,width):
        inset=self.style().pixelMetric(QStyle.PixelMetric.PM_IndicatorWidth,None,self)+12
        height=self.fontMetrics().boundingRect(QRect(0,0,max(1,width-inset),10000),Qt.TextFlag.TextWordWrap,self.text()).height()
        return max(24,height+8)
    def sizeHint(self):return QSize(260,self.heightForWidth(260))
    def minimumSizeHint(self):return QSize(80,self.heightForWidth(260))
    def hitButton(self,point):return self.rect().contains(point)
    def paintEvent(self,event):
        option=QStyleOptionButton();self.initStyleOption(option);option.text=''
        p=QPainter(self);self.style().drawControl(QStyle.ControlElement.CE_CheckBox,option,p,self)
        inset=self.style().pixelMetric(QStyle.PixelMetric.PM_IndicatorWidth,option,self)+12
        p.setPen(self.palette().color(QPalette.ColorRole.WindowText));p.setFont(self.font())
        p.drawText(self.rect().adjusted(inset,4,-4,-4),Qt.TextFlag.TextWordWrap|Qt.AlignmentFlag.AlignVCenter,self.text());p.end()
