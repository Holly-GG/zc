"""Settings choices change on explicit selection, never by scrolling past them."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox,QSpinBox
class ClickSelectComboBox(QComboBox):
    def __init__(self,parent=None):
        super().__init__(parent);self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
    def wheelEvent(self,event):event.ignore()
    def keyPressEvent(self,event):
        if event.key()==Qt.Key.Key_Escape:self.hidePopup();event.accept()
        else:event.ignore()

class ExplicitSpinBox(QSpinBox):
    def wheelEvent(self,event):event.ignore()
