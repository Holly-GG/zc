"""Compact work conversation and independent focus/todo desktop cards."""
import html,time
from PySide6.QtCore import Qt,QTimer,QPoint
from PySide6.QtGui import QPixmap,QRegion
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,QTextBrowser,QListWidget,QListWidgetItem,QSpinBox,QTabWidget,QCheckBox
from .art import asset_path
from .dialogue import choose,respond,context_for
from .geometry import Rect,nearest_area,clamp_position
from .theme import STYLE as PAPER
class DeskPanel(QWidget):
    def __init__(self,pet,title,size,key):
        super().__init__(None,Qt.WindowType.Tool|Qt.WindowType.WindowStaysOnTopHint)
        self.pet=pet;self.key=key;self.setObjectName("lifeRoot");self.setWindowTitle(title);area=self.screen().availableGeometry();self.resize(min(size[0],area.width()-24),min(size[1],area.height()-60));self.setStyleSheet(PAPER)
        self.layout=QVBoxLayout(self);self.layout.setContentsMargins(12,10,12,10)
        self.heading=QLabel(title);self.heading.setToolTip('拖动标题栏移动，关闭后保留桌宠');self.heading.setObjectName("brand");self.layout.addWidget(self.heading)
        self.last_pos=None
    def showEvent(self,event):
        point=self.pet.settings.data.get(self.key)
        if isinstance(point,list) and len(point)==2:x,y=point
        else:
            p=self.pet;area=nearest_area(p.x(),p.y(),p.areas());x,y=p.x()-self.width()-12,p.y()
            candidates=[(x,y),(p.x()+p.width()+12,p.y()),(p.x(),p.y()-self.height()-12),(p.x(),p.y()+p.height()+12)]
            for cx,cy in candidates:
                box=Rect(cx,cy,self.width(),self.height())
                if area.contains(box) and not box.intersects(p.rect_global()):x,y=cx,cy;break
        area=nearest_area(x,y,self.pet.areas());x,y=clamp_position(x,y,self.width(),self.height(),area);self.move(round(x),round(y));super().showEvent(event)
    def closeEvent(self,event):
        self.pet.settings.data[self.key]=[self.x(),self.y()];self.pet.settings.save();event.ignore();self.hide()
class WorkPanel(DeskPanel):
    def __init__(self,pet):
        super().__init__(pet,'年糕 · 桌面工作台',(360,460),'work_panel_position')
        self.busy=False;self.history=[];self.sent_count=0
        self.status=QLabel();self.status.setWordWrap(True);self.layout.addWidget(self.status)
        self.tabs=QTabWidget();self.layout.addWidget(self.tabs,1)
        chat=QWidget();chat.setObjectName("workTabPage");c=QVBoxLayout(chat);c.setContentsMargins(5,7,5,4)
        self.ai_enabled=QCheckBox('使用已配置 API 对话');self.ai_enabled.setChecked(pet.life.data['ai']['enabled']);self.ai_enabled.toggled.connect(self.set_api);c.addWidget(self.ai_enabled)
        self.log=QTextBrowser();self.log.setMinimumHeight(110);c.addWidget(self.log,1)
        label=QLabel('对话输入');label.setObjectName('eyebrow');c.addWidget(label)
        self.text=QLineEdit();self.text.setObjectName('workChatInput');self.text.setPlaceholderText('输入问题，按回车发送给年糕…');self.text.returnPressed.connect(self.send);c.addWidget(self.text)
        row=QHBoxLayout();c.addLayout(row)
        self.send_button=QPushButton('发送对话');self.send_button.clicked.connect(self.send);row.addWidget(self.send_button,1)
        self.clear_button=QPushButton('清空对话');self.clear_button.clicked.connect(self.clear_chat);row.addWidget(self.clear_button)
        self.tabs.addTab(chat,'API 对话')
        finder=QWidget();finder.setObjectName("workTabPage");s=QVBoxLayout(finder);s.setContentsMargins(5,7,5,4)
        hint=QLabel('搜索应用功能、物品、动作和你填写的待办。');hint.setWordWrap(True);hint.setObjectName('sub');s.addWidget(hint)
        self.search_input=QLineEdit();self.search_input.setObjectName('workSearchInput');self.search_input.setPlaceholderText('例如：喝水、猫砂、DeepSeek、工作');self.search_input.textChanged.connect(self.find);s.addWidget(self.search_input)
        self.search_results=QListWidget();self.search_results.itemClicked.connect(self.open_result);s.addWidget(self.search_results,1)
        self.search_notice=QLabel('搜索在本机完成，点击结果打开对应页面。');self.search_notice.setWordWrap(True);self.search_notice.setObjectName('sub');s.addWidget(self.search_notice)
        self.tabs.addTab(finder,'应用搜索')
        row=QHBoxLayout();self.layout.addLayout(row)
        for title,callback in [('API 设置',self.open_settings),('专注小窗',pet.open_focus),('退出工作模式',lambda:pet.set_work_mode(False))]:
            button=QPushButton(title);button.setObjectName('quiet');button.clicked.connect(callback);row.addWidget(button)
        self.reply('输入问题就能和我聊天；也可以切到应用搜索，找功能、物品和待办。')
        self.refresh_status()
    def showEvent(self,event):
        super().showEvent(event)
        self.ai_enabled.blockSignals(True);self.ai_enabled.setChecked(self.pet.life.data['ai']['enabled']);self.ai_enabled.blockSignals(False)
        self.refresh_status();(self.text if self.tabs.currentIndex()==0 else self.search_input).setFocus()
    def sync_config(self):
        self.ai_enabled.blockSignals(True);self.ai_enabled.setChecked(self.pet.life.data['ai']['enabled']);self.ai_enabled.blockSignals(False)
        if not self.busy:self.refresh_status()
    def refresh_status(self):
        ai=self.pet.life.data['ai']
        self.status.setText(('API 对话已开启 · '+ai['model']) if ai['enabled'] else '当前为本地回应 · 勾选 API 对话可使用已配置接口')
    def set_api(self,enabled):
        self.pet.life.data['ai']['enabled']=bool(enabled);self.pet.life.save();self.refresh_status()
        if self.pet.life_window:self.pet.life_window.ai_enabled.setChecked(bool(enabled))
    def open_settings(self):self.pet.open_life();self.pet.life_window.nav.setCurrentRow(7)
    def find(self,query):
        from .work_search import search
        self.search_results.clear();results=search(query,self.pet.life.data['tasks'])
        for result in results:
            item=QListWidgetItem(result['title']);item.setData(Qt.ItemDataRole.UserRole,result);self.search_results.addItem(item)
        self.search_notice.setText(('找到 '+str(len(results))+' 项，点击打开。') if results else '未找到匹配项。' if query.strip() else '搜索在本机完成，点击结果打开对应页面。')
    def open_result(self,item):
        result=item.data(Qt.ItemDataRole.UserRole)
        if not result:return
        self.pet.open_life();ui=self.pet.life_window;ui.nav.setCurrentRow(result['page'])
        if result['kind']=='action':
            ui.motion_group.setCurrentText('全部')
            if result['id'] in ui.motion_ids:ui.motion_list.setCurrentRow(ui.motion_ids.index(result['id']))
        if result['kind']=='item':
            owned=self.pet.life.data['inventory'].get(result['id'],0)>0
            if not owned:ui.nav.setCurrentRow(2);ui.shop_filter.setCurrentText('全部')
            cards=ui.bag_cards if owned else ui.shop_cards
            if result['id'] in cards:ui.stack.widget(3 if owned else 2).ensureWidgetVisible(cards[result['id']])
        if result['kind']=='task':
            ui.render_tasks()
            for i in range(ui.tasks.count()):
                item=ui.tasks.item(i)
                if item.data(Qt.ItemDataRole.UserRole)==result['id']:ui.tasks.setCurrentRow(i);ui.tasks.scrollToItem(item);break
    def clear_chat(self):
        if self.busy:return
        self.history.clear();self.log.clear();self.reply('新的一页，想聊什么？')
    def reply(self,text):self.log.append('<p style="color:#507669;margin:6px 0;"><b>年糕</b> · '+html.escape(str(text))+'</p>')
    def send(self):
        if self.busy:return
        text=self.text.text().strip()[:1000]
        if not text:return
        self.sent_count+=1;self.text.clear();self.log.append('你：'+html.escape(text));self.pet.autonomy.click()
        if not self.pet.life.data['ai']['enabled']:
            self.refresh_status();self.reply('[本地回应] '+respond(text));return
        from .life.ai import AIClient
        from .life.jobs import run_job
        self.busy=True;self.text.setEnabled(False);self.send_button.setEnabled(False);self.clear_button.setEnabled(False);self.ai_enabled.setEnabled(False)
        self.status.setText('API 正在回复 · 已附带最新性格、习惯和年龄…')
        client=AIClient(dict(self.pet.life.data['ai']),self.pet.vault,self.pet.life.profile_snapshot);history=list(self.history)
        def restore():
            self.busy=False;self.text.setEnabled(True);self.send_button.setEnabled(True);self.clear_button.setEnabled(True);self.ai_enabled.setEnabled(True);self.sync_config()
            self.text.setFocus()
        def done(reply):
            if self.pet.shutting_down:return
            restore();self.status.setText('API 回复成功 · '+client.settings['model']);self.reply('[API] '+reply)
            if self.pet.life.data['preferences']['network_time'] and client.server_time:self.pet.life.calibrate_time(client.server_time)
            self.history.extend([{'role':'user','content':text},{'role':'assistant','content':reply}]);self.history=self.history[-8:]
        def failed(error):
            if self.pet.shutting_down:return
            restore();self.status.setText('API 请求失败：'+str(error));self.reply('这条没有收到 API 回复，请检查提示后重试。');self.text.setText(text)
        run_job(lambda:client.chat(text,self.pet.life.mood,history),done,failed)
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
