from datetime import date
from PySide6.QtCore import QDate, QLocale, Qt, QRect
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QCalendarWidget
from .calendar_cn import china_now,lunar_label
from ..theme import TOKENS
class ChineseCalendar(QCalendarWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setLocale(QLocale(QLocale.Language.Chinese,QLocale.Country.China))
        self.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.setDateRange(QDate(2020,1,1),QDate(2069,12,31))
        self.setVerticalHeaderFormat(self.VerticalHeaderFormat.NoVerticalHeader)
        day=china_now().date();self.setSelectedDate(QDate(day.year,day.month,day.day))
        self.setStyleSheet("QWidget#qt_calendar_navigationbar{background:"+TOKENS["vellum"]+";} QToolButton{background:"+TOKENS["vellum"]+";color:"+TOKENS["ink"]+";border:0;padding:4px;}")
        self.setMinimumHeight(280)
    def paintCell(self,painter,rect,day):
        painter.save()
        selected=day==self.selectedDate()
        painter.fillRect(rect,QColor(TOKENS["sky"] if selected else TOKENS["card"]))
        painter.setPen(QColor(TOKENS["ink"] if day.month()==self.monthShown() else "#A3AA91"))
        font=QFont(painter.font());font.setPixelSize(13);painter.setFont(font)
        painter.drawText(QRect(rect.x(),rect.y(),rect.width(),rect.height()//2),Qt.AlignmentFlag.AlignCenter,str(day.day()))
        value=date(day.year(),day.month(),day.day())
        try:label=lunar_label(value)
        except ValueError:label=""
        font.setPixelSize(12);painter.setFont(font);painter.setPen(QColor(TOKENS["forest"]))
        painter.drawText(QRect(rect.x(),rect.y()+rect.height()//2,rect.width(),rect.height()//2),Qt.AlignmentFlag.AlignCenter,label)
        painter.restore()
