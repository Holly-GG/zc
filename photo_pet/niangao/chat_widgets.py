"""Shared local history browser and token meter; no provider requests from UI refresh."""
import html,json
from pathlib import Path
from PySide6.QtCore import QDate,QTimer,Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QDateEdit,QListWidget,QListWidgetItem,QTextBrowser,QFileDialog,QComboBox
from .life.ai import AIClient
from .life.token_budget import policy
class TokenMeter(QLabel):
    def __init__(self,pet,channel,input_field):
        super().__init__();self.pet=pet;self.channel=channel;self.input=input_field;self.setWordWrap(True);self.setObjectName('sub');self.setStyleSheet('font-size:12px;')
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.setInterval(180);self.timer.timeout.connect(self.refresh);input_field.textChanged.connect(lambda _text:self.timer.start())
        self.pulse=QTimer(self);self.pulse.timeout.connect(self.refresh);self.pulse.start(1500);self.refresh()
    def refresh(self):
        if self.pet.shutting_down:return
        settings=self.pet.life.data['ai']
        try:
            client=AIClient(settings,self.pet.vault,self.pet.life.profile_snapshot);count=self.channel.preview(client,self.input.text())
            rule=policy(settings);daily=self.pet.chat_store.daily();limit=settings['daily_token_limit'];left=max(0,limit-daily['total']);warning=daily['total']>=limit*settings['daily_warning_percent']/100
            self.setText(f"messages ≈ {count['estimated']:,} token（估算） · 保守预算 {count['conservative']:,} / 阈值 {rule['threshold']:,}\n今日已计 {daily['total']:,} / {limit:,} · 剩余 {left:,}"+(" · 余量偏低" if warning else '')+f"\n服务端实际 {daily['actual']:,} + 估算/预留 {daily['estimated']:,}；不是账户余额")
        except (ValueError,OSError) as error:self.setText('Token 状态：'+str(error))
class SessionChooser(QWidget):
    def __init__(self,pet,channel,changed,busy=lambda:False):
        super().__init__();self.pet=pet;self.channel=channel;self.changed=changed;self.busy=busy
        row=QHBoxLayout(self);row.setContentsMargins(0,0,0,0);from .ui_controls import ClickSelectComboBox
        self.combo=ClickSelectComboBox();self.combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon);self.combo.setMinimumContentsLength(12);self.combo.setMinimumWidth(80);row.addWidget(self.combo,1)
        self.new_button=QPushButton('新会话');row.addWidget(self.new_button);self.new_button.clicked.connect(self.new);self.combo.activated.connect(self.selected);self.refresh()
    def refresh(self):
        if not self.busy():self.channel.select(self.pet.life.data['ai'])
        self.combo.blockSignals(True);self.combo.clear()
        for s in self.pet.chat_store.list_sessions(self.channel.channel):
            if s['identity']!=self.channel.identity:continue
            self.combo.addItem(s['created'][5:16].replace('T',' ')+' · '+s['model']+' · '+s['id'][:5],s['id'])
        index=self.combo.findData(self.channel.session_id)
        if index>=0:self.combo.setCurrentIndex(index)
        self.combo.blockSignals(False)
    def new(self):
        if self.busy():return
        self.channel.new(self.pet.life.data['ai']);self.refresh();self.changed()
    def selected(self,index):
        if self.busy():
            self.combo.setCurrentIndex(max(0,self.combo.findData(self.channel.session_id)));return
        id=self.combo.itemData(index);session=self.pet.chat_store.get_session(id)
        if not session:return
        from .life.token_budget import identity
        if session['identity']!=identity(self.pet.life.data['ai']):
            # Historical provider sessions remain readable, but cannot silently send to another model.
            self.changed(id);self.refresh();return
        self.channel.session_id=id;self.channel.identity=session['identity']
        with self.pet.chat_store.db() as db:db.execute('INSERT OR REPLACE INTO active VALUES(?,?,?)',(self.channel.channel,session['identity'],id))
        self.changed()
class HistoryBrowser(QWidget):
    def __init__(self,pet):
        super().__init__();self.pet=pet;self.offset=0
        l=QVBoxLayout(self);l.setContentsMargins(5,5,5,5);row=QHBoxLayout();l.addLayout(row)
        self.day=QDateEdit();self.day.setCalendarPopup(True);from .life.calendar_cn import china_now
        now=pet.life.now();self.day.setDate(QDate(now.year,now.month,now.day));self.day.dateChanged.connect(self.reset);row.addWidget(self.day)
        for name,callback in [('前页',lambda:self.page(-100)),('后页',lambda:self.page(100)),('刷新',self.reset)]:
            b=QPushButton(name);b.setObjectName('quiet');b.clicked.connect(callback);row.addWidget(b)
        self.rows=QListWidget();self.rows.setMaximumHeight(125);self.rows.itemClicked.connect(self.open_message);l.addWidget(self.rows)
        self.view=QTextBrowser();l.addWidget(self.view,1);self.hint=QLabel('按中国日期检索全部本地聊天；每页100条，选中可看完整正文。');self.hint.setWordWrap(True);self.hint.setObjectName('sub');l.addWidget(self.hint)
        b=QPushButton('导出全部历史 JSON');b.clicked.connect(self.export);l.addWidget(b);self.reset()
    def reset(self,*_):self.offset=0;self.load()
    def page(self,delta):self.offset=max(0,self.offset+delta);self.load()
    def load(self):
        records=self.pet.chat_store.by_day(self.day.date().toString('yyyy-MM-dd'),self.offset,100);self.rows.clear()
        for r in records:
            label=r['created'][11:19]+' · '+{'main':'生活馆','work':'桌面'}.get(r['channel'],r['channel'])+' · '+{'user':'你','assistant':'年糕','system':'摘要/提示'}.get(r['role'],r['role'])+' · '+r['content'].replace('\n',' ')[:35]
            item=QListWidgetItem(label);item.setData(Qt.ItemDataRole.UserRole,r);self.rows.addItem(item)
        self.hint.setText(f'第 {self.offset+1}–{self.offset+len(records)} 条 · 选中查看完整正文，完整数据不会自动删除。')
    def open_message(self,item):
        r=item.data(Qt.ItemDataRole.UserRole);self.view.setPlainText(r['created']+' · '+r['model']+' · '+r['state']+'\n\n'+r['content'])
    def export(self):
        path,_=QFileDialog.getSaveFileName(self,'导出聊天历史','年糕聊天历史.json','JSON (*.json)')
        if not path:return
        try:self.pet.chat_store.export_json(path);self.hint.setText('已导出全部历史：'+path)
        except OSError as error:self.hint.setText('导出失败：'+str(error))
def transcript_html(store,id):
    session=store.get_session(id);parts=[]
    if session and session['summary']:parts.append('<p><b>承接摘要（原始对话仍在历史中）</b><br>'+html.escape(session['summary']).replace('\n','<br>')+'</p>')
    # The live pane shows the most recent page; date history can retrieve every message.
    with store.db() as db:rows=[dict(r) for r in db.execute('SELECT * FROM messages WHERE session=? ORDER BY id DESC LIMIT 150',(id,))][::-1]
    for r in rows:
        name={'user':'你','assistant':'年糕','system':'承接摘要'}.get(r['role'],r['role'])
        state={'pending':'等待回复','failed':'请求未完成','transferred':'已转入新会话','complete':''}.get(r['state'],'')
        marker='[API] ' if r['source'] in ('api','summary') and r['role']!='user' else '[本地回应] ' if r['source']=='local' and r['role']=='assistant' else ''
        body='<span style="font-size:12px;color:#66745C">'+html.escape(name+' · '+r['created'][11:19]+' '+state)+'</span><br>'+marker+html.escape(r['content']).replace('\n','<br>')
        color='#E1EFF7' if r['role']=='user' else '#EDF0DA' if r['role']=='assistant' else '#F4F0E2'
        cell='<td width="76%" bgcolor="'+color+'" style="color:#2A472F">'+body+'</td>';space='<td width="24%"></td>'
        parts.append('<table width="100%" cellpadding="10" cellspacing="0"><tr>'+(space+cell if r['role']=='user' else cell+space)+'</tr></table><p style="margin:6px"></p>')
    return ''.join(parts) or '<p>新会话，聊天记录将保存在本机。</p>'
