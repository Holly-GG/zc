"""Local photo import and date archive UI. No API access, no source-file deletion."""
import sqlite3,threading
from PySide6.QtCore import Qt,QDate,QTimer,QSize,QRectF
from PySide6.QtGui import QPixmap,QImageReader,QPainter,QColor,QPen
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QComboBox,QLineEdit,QDateEdit,
 QCheckBox,QFileDialog,QDialog,QFormLayout,QTextEdit,QMessageBox,QFrame,QScrollArea)
from .life.album import AlbumStore,CATEGORIES
from .life.jobs import run_job
from .journal_components import CardGrid,FeedbackLabel

class PhotoPreview(QPushButton):
    def __init__(self,pixmap):
        super().__init__();self.picture=pixmap;self.setObjectName('photoPreview');self.setMinimumHeight(150)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        fill='#DCE3C5' if self.isDown() else '#E8E9C0' if self.underMouse() else '#F5F1DE'
        p.setPen(QPen(QColor('#3E7197' if self.hasFocus() else '#D0C49E'),2 if self.hasFocus() else 1));p.setBrush(QColor(fill));p.drawRect(QRectF(1,1,self.width()-2,self.height()-2))
        if self.picture.isNull():
            p.setPen(QColor('#66745C'));p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,'预览不可用')
        else:
            size=self.picture.size();size.scale(QSize(max(1,self.width()-10),self.height()-10),Qt.AspectRatioMode.KeepAspectRatio)
            p.drawPixmap(QRectF((self.width()-size.width())/2,(self.height()-size.height())/2,size.width(),size.height()),self.picture,QRectF(self.picture.rect()))
        p.end()

class AlbumPage(QWidget):
    def __init__(self,pet,notice):
        super().__init__();self.pet=pet;self.notice=notice;self.busy=False;self.offset=0;self.per_page=12;self.cancel_event=threading.Event()
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(10)
        try:self.store=AlbumStore(pet.settings.path.parent/'album',pet.life.now)
        except (OSError,sqlite3.Error) as exc:
            label=QLabel('相册暂时无法打开：'+str(exc));label.setWordWrap(True);layout.addWidget(label);self.store=None;return
        row=QHBoxLayout();layout.addLayout(row)
        self.import_button=QPushButton('导入照片');self.import_button.setObjectName('primary');self.import_button.clicked.connect(self.choose_files);row.addWidget(self.import_button)
        self.cancel_button=QPushButton('取消');self.cancel_button.hide();self.cancel_button.clicked.connect(self.cancel_import);row.addWidget(self.cancel_button)
        self.manual=QCheckBox('指定归档日期');row.addWidget(self.manual)
        now=pet.life.now();self.day=QDateEdit(QDate(now.year,now.month,now.day));self.day.setCalendarPopup(True);self.day.setDisplayFormat('yyyy-MM-dd');self.day.setDateRange(QDate(1,1,1),QDate(9999,12,31));self.day.setEnabled(False);self.manual.toggled.connect(self.day.setEnabled);row.addWidget(self.day);row.addStretch()
        hint=QLabel('仅保存本机副本 · JPEG拍摄日期优先；其他图片或缺失时采用文件日期 · 日期可修改');hint.setObjectName('sub');hint.setWordWrap(True);layout.addWidget(hint)
        row=QHBoxLayout();layout.addLayout(row)
        self.month=QComboBox();self.month.setMinimumWidth(110);row.addWidget(self.month)
        self.category=QComboBox();self.category.addItem('全部分类','');[self.category.addItem(c,c) for c in CATEGORIES];row.addWidget(self.category)
        self.order=QComboBox();self.order.addItem('日期：新到旧',False);self.order.addItem('日期：旧到新',True);row.addWidget(self.order)
        self.search=QLineEdit();self.search.setPlaceholderText('搜索标题或备注');self.search.setMaxLength(200);layout.addWidget(self.search)
        for combo in (self.month,self.category,self.order):combo.currentIndexChanged.connect(self.reset)
        self.debounce=QTimer(self);self.debounce.setSingleShot(True);self.debounce.setInterval(180);self.debounce.timeout.connect(self.reset);self.search.textChanged.connect(lambda _:self.debounce.start())
        self.status=FeedbackLabel();layout.addWidget(self.status)
        self.grid=CardGrid(153);layout.addWidget(self.grid)
        self.empty=QLabel('还没有照片。点击“导入照片”，为年糕收藏一个小日子。');self.empty.setWordWrap(True);self.empty.setObjectName('emptyState');layout.addWidget(self.empty)
        row=QHBoxLayout();layout.addLayout(row);self.previous=QPushButton('上一页');self.next=QPushButton('下一页');row.addWidget(self.previous);row.addWidget(self.next);row.addStretch()
        self.previous.clicked.connect(lambda:self.page(-self.per_page));self.next.clicked.connect(lambda:self.page(self.per_page))
        self.rebuild_months();self.refresh()
    def rebuild_months(self):
        selected=self.month.currentData();self.month.blockSignals(True);self.month.clear();self.month.addItem('全部日期','')
        for month,count in self.store.months():self.month.addItem(f'{month} · {count}张',month)
        self.month.setCurrentIndex(max(0,self.month.findData(selected)));self.month.blockSignals(False)
    def reset(self,*_):self.offset=0;self.refresh()
    def page(self,amount):self.offset=max(0,self.offset+amount);self.refresh()
    def refresh(self):
        if not self.store:return
        records,total=self.store.query(self.month.currentData() or '',self.category.currentData() or '',self.search.text(),self.offset,self.per_page,bool(self.order.currentData()))
        if not records and self.offset:self.offset=max(0,self.offset-self.per_page);return self.refresh()
        for old in self.grid.cards:old.deleteLater()
        cards=[]
        for record in records:
            card=QFrame();card.setObjectName('photoCard');card.setMinimumWidth(145);body=QVBoxLayout(card);body.setContentsMargins(10,10,10,12)
            path=self.store.owned(record['thumbnail']);pix=QPixmap(str(path)) if path.exists() else QPixmap()
            button=PhotoPreview(pix)
            button.setAccessibleName('查看照片：'+record['title']);button.clicked.connect(lambda checked=False,id=record['id']:self.open_photo(id));body.addWidget(button)
            label=QLabel(record['day']+' · '+record['category']);label.setObjectName('eyebrow');body.addWidget(label)
            label=QLabel(record['title']);label.setTextFormat(Qt.TextFormat.PlainText);label.setWordWrap(True);label.setObjectName('productName');body.addWidget(label)
            edit=QPushButton('查看 / 编辑');edit.clicked.connect(lambda checked=False,id=record['id']:self.open_photo(id));body.addWidget(edit);cards.append(card)
        self.grid.set_cards(cards);self.empty.setVisible(not records);self.previous.setEnabled(self.offset>0);self.next.setEnabled(self.offset+len(records)<total)
        self.status.setText(f'本地归档 · 共 {total} 张'+(f' · 第 {self.offset+1}–{self.offset+len(records)} 张' if records else ''))
    def choose_files(self):
        if self.busy:return
        paths,_=QFileDialog.getOpenFileNames(self,'导入照片到本地相册','','图片 (*.jpg *.jpeg *.png *.webp *.bmp *.gif)')
        if paths:self.import_paths(paths)
    def import_paths(self,paths):
        if self.busy or not self.store:return
        if len(paths)>256:self.status.setText('每次最多导入256张，请分批选择。');return
        self.busy=True;self.cancel_event.clear();self.import_button.setEnabled(False);self.cancel_button.show();self.manual.setEnabled(False);self.day.setEnabled(False);self.status.setText('正在生成预览并保存本地副本…')
        override=self.day.date().toString('yyyy-MM-dd') if self.manual.isChecked() else None
        def restored():self.busy=False;self.import_button.setEnabled(True);self.cancel_button.hide();self.manual.setEnabled(True);self.day.setEnabled(self.manual.isChecked())
        def done(result):
            if self.pet.shutting_down:return
            restored();self.rebuild_months();self.reset();self.last_result=result
            text=f"已导入 {len(result['imported'])} 张 · 重复 {len(result['duplicates'])} 张 · 失败 {len(result['errors'])} 张"
            if result['cancelled']:text='导入已取消 · '+text
            if result['errors']:text+='\n'+'\n'.join(r['name']+'：'+r['error'] for r in result['errors'][:5])
            self.status.show_message(text,'warning' if result['errors'] else 'info');self.notice(text.splitlines()[0])
        def failed(message):
            if self.pet.shutting_down:return
            restored();self.status.show_message('导入未完成：'+message,'error')
        run_job(lambda:self.store.import_files(paths,override,self.cancel_event),done,failed)
    def cancel_import(self):
        self.cancel_event.set()
        if self.busy:self.status.setText('正在取消，已归档的照片会保留。')
    def open_photo(self,id):
        record=self.store.get(id)
        if not record:return
        dialog=QDialog(self);dialog.setWindowTitle('照片详情 · '+record['day']);area=self.screen().availableGeometry();dialog.resize(min(590,area.width()-32),min(720,area.height()-40));outer=QVBoxLayout(dialog)
        scroll=QScrollArea();scroll.setWidgetResizable(True);outer.addWidget(scroll);content=QWidget();layout=QVBoxLayout(content);scroll.setWidget(content)
        picture=QLabel();picture.setAlignment(Qt.AlignmentFlag.AlignCenter);picture.setMinimumHeight(180);reader=QImageReader(str(self.store.owned(record['original'])));reader.setAutoTransform(True);size=reader.size();reader.setScaledSize(size.scaled(QSize(510,290),Qt.AspectRatioMode.KeepAspectRatio));image=reader.read();del reader
        if image.isNull():picture.setText('原图副本暂时无法读取；归档信息仍保留。')
        else:picture.setPixmap(QPixmap.fromImage(image))
        layout.addWidget(picture);form=QFormLayout();layout.addLayout(form)
        title=QLineEdit(record['title']);title.setMaxLength(120);form.addRow('照片标题',title)
        day=QDateEdit(QDate.fromString(record['day'],'yyyy-MM-dd'));day.setDateRange(QDate(1,1,1),QDate(9999,12,31));day.setCalendarPopup(True);day.setDisplayFormat('yyyy-MM-dd');form.addRow('归档日期',day)
        category=QComboBox();category.addItems(CATEGORIES);category.setCurrentText(record['category']);form.addRow('分类',category)
        note=QTextEdit();note.setPlainText(record['note']);note.setMaximumHeight(80);form.addRow('备注',note)
        label=QLabel('日期来源：'+record['date_source']+'\n原始文件：'+record['original_name']);label.setTextFormat(Qt.TextFormat.PlainText);label.setWordWrap(True);label.setObjectName('sub');layout.addWidget(label)
        feedback=QLabel();feedback.setWordWrap(True);layout.addWidget(feedback)
        row=QHBoxLayout();layout.addLayout(row)
        def save():
            try:self.store.update(id,title.text(),day.date().toString('yyyy-MM-dd'),category.currentText(),note.toPlainText());self.rebuild_months();self.refresh();dialog.accept()
            except (OSError,ValueError,sqlite3.Error) as exc:feedback.setText('保存失败：'+str(exc))
        def export():
            path,_=QFileDialog.getSaveFileName(dialog,'导出原图副本',record['original_name'])
            if not path:return
            try:self.store.export_original(id,path);feedback.setText('原图副本已导出。')
            except (OSError,ValueError) as exc:feedback.setText('导出失败：'+str(exc))
        def remove():
            answer=QMessageBox.question(dialog,'从相册移除','仅删除本相册中的副本，您最初选择的原文件不会删除。确定移除？')
            if answer!=QMessageBox.StandardButton.Yes:return
            try:
                retained=self.store.remove(id);self.rebuild_months();self.refresh()
                if retained:self.status.setText('已从相册移除；部分副本正被占用，文件仍保留在本机相册目录。')
                dialog.accept()
            except (OSError,sqlite3.Error) as exc:feedback.setText('移除失败：'+str(exc))
        for text,callback,name in [('保存修改',save,'primary'),('导出原图',export,'quiet'),('从相册移除',remove,'danger')]:
            button=QPushButton(text);button.setObjectName(name);button.clicked.connect(callback);row.addWidget(button)
        dialog.exec()
