"""Compact work conversation and independent focus/todo desktop cards."""
import html,time
from PySide6.QtCore import Qt,QTimer,QPoint
from PySide6.QtGui import QPixmap,QRegion
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,QTextBrowser,QListWidget,QListWidgetItem,QSpinBox
from .art import asset_path
from .dialogue import choose,respond,context_for
from .geometry import nearest_area,clamp_position
from .theme import STYLE as PAPER
class DeskPanel(QWidget):
    def __init__(self,pet,title,size,key):
        super().__init__(None,Qt.WindowType.Tool|Qt.WindowType.WindowStaysOnTopHint)
        self.pet=pet;self.key=key;self.setObjectName("lifeRoot");self.setWindowTitle(title);self.resize(*size);self.setStyleSheet(PAPER)
        self.layout=QVBoxLayout(self);self.layout.setContentsMargins(12,10,12,10)
        self.heading=QLabel(title);self.heading.setToolTip('拖动标题栏移动，关闭后保留桌宠');self.heading.setObjectName("brand");self.layout.addWidget(self.heading)
        self.last_pos=None
    def showEvent(self,event):
        point=self.pet.settings.data.get(self.key)
        x,y=point if isinstance(point,list) and len(point)==2 else (self.pet.x()-self.width()-12,self.pet.y())
        area=nearest_area(x,y,self.pet.areas());x,y=clamp_position(x,y,self.width(),self.height(),area);self.move(round(x),round(y));super().showEvent(event)
    def closeEvent(self,event):
        self.pet.settings.data[self.key]=[self.x(),self.y()];self.pet.settings.save();event.ignore();self.hide()
class WorkPanel(DeskPanel):
    def __init__(self,pet):
        super().__init__(pet,'年糕 · 安静陪伴',(320,400),'work_panel_position')
        self.status=QLabel('离线也能陪伴；联网聊天需在设置中启用 API');self.status.setWordWrap(True);self.layout.addWidget(self.status)
        self.pose_label=QLabel('随机轻待机 / 不走动 / 点击回应');self.pose_label.setObjectName('chip');self.layout.addWidget(self.pose_label)
        self.log=QTextBrowser();self.log.setMinimumHeight(80);self.layout.addWidget(self.log)
        self.text=QLineEdit();self.text.setPlaceholderText('和年糕说句话…');self.text.returnPressed.connect(self.send);self.layout.addWidget(self.text)
        row=QHBoxLayout();self.layout.addLayout(row)
        self.send_button=QPushButton('发送');self.send_button.clicked.connect(self.send);row.addWidget(self.send_button)
        for title,callback in [('摸摸',lambda:self.reply(choose('pet'))),('专注',pet.open_focus),('生活馆',pet.open_life)]:
            button=QPushButton(title);button.clicked.connect(callback);row.addWidget(button)
        button=QPushButton('退出工作模式');button.clicked.connect(lambda:pet.set_work_mode(False));self.layout.addWidget(button)
        self.history=[];self.reply('工作模式换成轻轻动的年糕啦。不走动，点我就陪你聊天。')
    def reply(self,text):self.log.append('<p style="color:#507669;margin:6px 0;"><b>年糕</b> · '+html.escape(str(text))+'</p>')
    def send(self):
        text=self.text.text().strip()[:1000]
        if not text:return
        self.text.clear();self.log.append('你：'+html.escape(text));self.pet.autonomy.click()
        if not self.pet.life.data['ai']['enabled']:self.reply(respond(text));return
        from .life.ai import AIClient
        from .life.jobs import run_job
        self.send_button.setEnabled(False);self.status.setText('正在连接已配置的 API；每次读取最新年糕档案…')
        client=AIClient(self.pet.life.data['ai'],self.pet.vault,self.pet.life.profile_snapshot)
        def done(reply):
            self.send_button.setEnabled(True);self.status.setText('API 已连接 · 性格、习惯和年龄已作为本次前提');self.reply(reply)
            if self.pet.life.data["preferences"]["network_time"] and client.server_time:self.pet.life.calibrate_time(client.server_time)
            self.history.extend([{'role':'user','content':text},{'role':'assistant','content':reply}]);self.history=self.history[-8:]
        def failed(error):
            self.send_button.setEnabled(True);self.status.setText(str(error));self.reply(choose('offline'))
        run_job(lambda:client.chat(text,self.pet.life.mood,list(self.history)),done,failed)
class FocusPanel(DeskPanel):
    def __init__(self,pet):
        super().__init__(pet,'年糕 · 专注与待办',(300,360),'focus_position')
        self.clock=QLabel();self.clock.setStyleSheet('font-size:28px;color:#305e63');self.layout.addWidget(self.clock)
        row=QHBoxLayout();self.layout.addLayout(row);self.minutes=QSpinBox();self.minutes.setRange(1,180);self.minutes.setValue(25);self.minutes.setSuffix(' 分');row.addWidget(self.minutes)
        for title,fn in [('开始',lambda:pet.life.focus_start(self.minutes.value())),('暂停',pet.life.focus_pause),('继续',pet.life.focus_resume)]:
            button=QPushButton(title);button.clicked.connect(fn);row.addWidget(button)
        self.tasks=QListWidget();self.tasks.itemChanged.connect(self.complete);self.layout.addWidget(self.tasks)
        self.entry=QLineEdit();self.entry.setPlaceholderText('添加待办，按回车');self.entry.returnPressed.connect(self.add);self.layout.addWidget(self.entry)
        hint=QLabel('仅匹配你填写的待办关键词，不读取屏幕内容。');hint.setWordWrap(True);self.layout.addWidget(hint)
        self.signature=None;self.encounters=set();self.next_encounter=0
        self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(500);self.refresh()
    def add(self):
        text=self.entry.text().strip()
        if self.pet.life.add_task(text):self.entry.clear();self.pet.bubble.speak(respond(text),self.pet.rect_global(),self.pet.areas());self.refresh()
    def complete(self,item):
        if item.checkState()==Qt.CheckState.Checked and self.pet.life.complete_task(item.data(Qt.ItemDataRole.UserRole)):
            self.pet.say('done');self.refresh()
    def refresh(self):
        focus=self.pet.life.data['focus'];seconds=focus['remaining'];self.clock.setText(f'{seconds//60:02d}:{seconds%60:02d}'+(' · 专注' if focus['active'] else ' · 暂停'))
        tasks=self.pet.life.data['tasks'][-100:];signature=tuple((v['id'],v['done'],v['text']) for v in tasks)
        if signature!=self.signature:
            self.signature=signature;self.tasks.blockSignals(True);self.tasks.clear()
            for task in tasks:
                item=QListWidgetItem(task['text']);item.setData(Qt.ItemDataRole.UserRole,task['id']);item.setFlags(item.flags()|Qt.ItemFlag.ItemIsUserCheckable);item.setCheckState(Qt.CheckState.Checked if task['done'] else Qt.CheckState.Unchecked);self.tasks.addItem(item)
            self.tasks.blockSignals(False)
        if not self.isVisible() or self.pet.work_mode or time.monotonic()<self.next_encounter:return
        distance=(self.geometry().center()-self.pet.geometry().center()).manhattanLength()
        if distance<self.width()+self.pet.width():
            task=next((v for v in tasks if not v['done'] and v['id'] not in self.encounters and context_for(v['text'])!='todo'),None)
            if task:
                self.encounters.add(task['id']);self.next_encounter=time.monotonic()+90
                self.pet.bubble.speak(respond(task['text']),self.pet.rect_global(),self.pet.areas())
