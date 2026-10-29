"""Local-first multifunction dashboard. The desktop pet remains a separate window."""
import json,uuid,sys
from pathlib import Path
from datetime import date
from PySide6.QtCore import Qt,QTimer,QDate,QEvent
from PySide6.QtGui import QPixmap,QPainter,QColor
from PySide6.QtWidgets import (QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,
    QListWidget,QStackedWidget,QScrollArea,QProgressBar,QComboBox,QSpinBox,QDoubleSpinBox,QTextBrowser,
    QFrame,QLineEdit,QTextEdit,QCheckBox,QCalendarWidget,QFileDialog,QDateEdit,QGroupBox,QFormLayout)
from ..art import asset_path
from .engine import STAT_NAMES
from .catalog import BY_ID,is_placeable
from .profile import sanitize_profile
from .item_art import item_pixmap
from ..desktop_items import ItemDragCard
from ..ui_controls import ClickSelectComboBox
from .ai import SecretVault,AIClient,checked_base
from .jobs import run_job
from ..theme import STYLE
class PaperPage(QWidget):
    def paintEvent(self,event):
        p=QPainter(self);p.fillRect(self.rect(),QColor("#fbf7ef"));p.setPen(QColor("#e3e8dc"))
        for x in range(0,self.width(),22):p.drawPoint(x,10)
        for y in range(0,self.height(),22):
            for x in range(10,self.width(),22):p.drawPoint(x,y)
        p.end()
from ..interaction.actions import ACTIONS as MOTIONS,MOOD_POOLS,SOUNDS
ACTIONS={key:info.label for key,info in MOTIONS.items()}
PENDING=["跳上真实家具","精确三维攀爬与肢体接触","服饰穿戴","幼猫/老年独立模型","更连贯的长帧动作"]
class MoodCurve(QWidget):
    def __init__(self,engine):super().__init__();self.engine=engine;self.setMinimumHeight(110)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.fillRect(self.rect(),QColor("#e0eee7"))
        values=[e["value"] for e in self.engine.data["mood_history"][-80:]]
        if len(values)<2:p.setPen(QColor("#305E63"));p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,"陪伴一会儿，心情曲线就会长出来")
        else:
            p.setPen(QColor("#40A387"))
            from PySide6.QtCore import QPointF
            for i in range(1,len(values)):
                p.drawLine(QPointF(10+(i-1)*(self.width()-20)/(len(values)-1),self.height()-10-values[i-1]*(self.height()-20)/100),
                           QPointF(10+i*(self.width()-20)/(len(values)-1),self.height()-10-values[i]*(self.height()-20)/100))
        p.end()
class LifeWindow(QMainWindow):
    def __init__(self,pet):
        super().__init__();self.pet=pet;self.engine=pet.life;self.setWindowTitle("年糕生活馆 · NIANGAO");area=self.screen().availableGeometry();width=min(860,area.width()-24);height=min(650,area.height()-56);self.resize(width,height);self.setMinimumSize(min(740,width),min(540,height));self.setStyleSheet(STYLE)
        self.vault=pet.vault;self.client=AIClient(self.engine.data["ai"],self.vault,self.engine.profile_snapshot);self.history=[]
        base=QWidget();base.setObjectName("lifeRoot");self.setCentralWidget(base);outer=QVBoxLayout(base);outer.setContentsMargins(14,12,14,10);outer.setSpacing(10)
        header=QFrame();header.setObjectName("header");top=QHBoxLayout(header);brand=QVBoxLayout();top.addLayout(brand,1)
        label=QLabel("NIANGAO / 年糕的小日子");label.setObjectName("brand");brand.addWidget(label)
        self.clock_label=QLabel();self.clock_label.setObjectName("eyebrow");brand.addWidget(self.clock_label)
        for text,callback in [("随机待机",lambda:self.pet.set_work_mode(not self.pet.work_mode)),("专注小窗",self.pet.open_focus),("整理桌面",self.pet.desktop.clear)]:
            button=QPushButton(text);button.setObjectName("quiet");button.clicked.connect(callback);top.addWidget(button)
        outer.addWidget(header);row=QHBoxLayout();row.setSpacing(12);outer.addLayout(row,1)
        sidebar=QFrame();sidebar.setObjectName("sidebar");sidebar.setFixedWidth(142);side=QVBoxLayout(sidebar);side.setContentsMargins(9,13,9,9)
        mark=QLabel();mark.setAlignment(Qt.AlignmentFlag.AlignCenter);mark.setPixmap(QPixmap(str(asset_path("ui/niangao-mark.svg"))).scaled(64,64,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation));side.addWidget(mark)
        label=QLabel("小棕点值班室");label.setAlignment(Qt.AlignmentFlag.AlignCenter);label.setObjectName("eyebrow");side.addWidget(label)
        self.nav=QListWidget();self.nav.setObjectName("navigation");side.addWidget(self.nav,1);self.stack=QStackedWidget();row.addWidget(sidebar);row.addWidget(self.stack,1)
        self.status=QLabel("本地陪伴 · 档案随时保存 · 今天也慢慢来");self.status.setObjectName("sub");self.status.setWordWrap(True);outer.addWidget(self.status)
        builders=[("陪伴总览",self.overview),("照料与动作",self.care_page),("年糕小铺",self.shop_page),("我的背包",self.backpack_page),
                  ("专注与待办",self.focus_page),("和年糕聊天",self.chat_page),("年糕日记",self.diary_page),("性格与设置",self.settings_page)]
        for name,builder in builders:
            self.nav.addItem(name);page=PaperPage();layout=QVBoxLayout(page);builder(layout);layout.addStretch()
            scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(page);self.stack.addWidget(scroll)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex);self.nav.setCurrentRow(0)
        self.pet.desktop.changed.connect(self.refresh_inventory)
        self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(1000);self.refresh()
    def title(self,layout,title,subtitle=""):
        row=QHBoxLayout();layout.addLayout(row);texts=QVBoxLayout();row.addLayout(texts,1)
        label=QLabel(title);label.setObjectName("hero");texts.addWidget(label)
        if subtitle:
            label=QLabel(subtitle);label.setObjectName("sub");label.setWordWrap(True);texts.addWidget(label)
        art="care" if any(v in title for v in ("照顾","水","照料")) else "shop" if any(v in title for v in ("补给","小铺","背包")) else "diary" if any(v in title for v in ("日记","专注","休息")) else "welcome"
        image=QLabel();image.setFixedSize(84,80)
        path=asset_path("ui/"+art+".webp")
        image.setPixmap((QPixmap(str(path)) if path.exists() else item_pixmap("food_bowl",80)).scaled(84,80,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation));row.addWidget(image)
    def button(self,layout,text,callback):
        b=QPushButton(text);b.clicked.connect(lambda _checked=False:callback());layout.addWidget(b);return b
    def notice(self,text):self.status.setText(str(text))
    def result(self,result):self.notice(result[1]);self.refresh()
    def overview(self,l):
        self.title(l,"你好，今天也有年糕陪你","真实生日 · 照料记录 · 小小的陪伴奖励")
        row=QHBoxLayout();l.addLayout(row);photo=QLabel();photo.setPixmap((QPixmap(str(asset_path("ui/welcome.webp"))) if asset_path("ui/welcome.webp").exists() else item_pixmap("food_bowl",130)).scaled(135,155,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation));row.addWidget(photo)
        box=QVBoxLayout();row.addLayout(box,1);self.age_label=QLabel();self.age_label.setWordWrap(True);box.addWidget(self.age_label)
        self.summary=QLabel();box.addWidget(self.summary);self.bars={}
        for key,name in STAT_NAMES.items():
            line=QHBoxLayout();line.addWidget(QLabel(name));bar=QProgressBar();line.addWidget(bar,1);box.addLayout(line);self.bars[key]=bar
        actions=QHBoxLayout();l.addLayout(actions);self.button(actions,"每日陪伴打卡 +15",lambda:self.result(self.engine.checkin()));self.button(actions,"去一次五分钟虚拟旅行",lambda:self.result(self.engine.start_trip()))
        self.curve=MoodCurve(self.engine);l.addWidget(self.curve);self.events=QTextBrowser();self.events.setMaximumHeight(180);l.addWidget(self.events)
    def care_page(self,l):
        self.title(l,"照顾每一种小情绪","照料数值属于游戏，不代表现实健康诊断。每项照料有 20 秒冷却。")
        grid=QGridLayout();l.addLayout(grid)
        for i,(key,text,action) in enumerate([("meal","基础餐","feed"),("water","喝水","idle"),("pet","摸摸头","pet"),("play","逗猫玩","play_bow"),
             ("brush","梳毛","groom"),("bath","虚拟清洁","groom"),("litter","清猫砂","idle"),("rest","休息","sleep"),("checkup","虚拟健康照料","idle")]):
            b=QPushButton(text);grid.addWidget(b,i//3,i%3);b.clicked.connect(lambda checked=False,k=key,a=action:self.care(k,a))
        self.care_objects(l)
        live=QGroupBox("桌面照料 · 看得见的小日常");v=QVBoxLayout(live)
        hint=QLabel("粮袋 / 冻干：右键逐颗倒出，Shift + 右键打开菜单。食物落稳后轻点，年糕会走过去闻闻再吃。\n猫砂盆：轻点邀请使用，右键铲砂；离开前打断不会扣掉食物。");hint.setWordWrap(True);hint.setObjectName("sub");v.addWidget(hint)
        self.desktop_status=QLabel();self.desktop_status.setWordWrap(True);v.addWidget(self.desktop_status);l.addWidget(live)
        group=QGroupBox("动作与表情图鉴 · 照片关键帧");g=QVBoxLayout(group);l.addWidget(group)
        label=QLabel("轻点：摸头；按住约 0.85 秒：轻啃指尖；左键拖拽：抱起；Shift + 左键滑动：抚摸；双击：戳一下。\n照片关键帧表现动作，较大变姿仍有跳变。");label.setWordWrap(True);g.addWidget(label)
        self.motion_group=QComboBox();self.motion_group.addItems(["全部"]+sorted(set(info.group for info in MOTIONS.values())));g.addWidget(self.motion_group)
        self.motion_list=QListWidget();self.motion_list.setMinimumHeight(200);self.motion_list.currentRowChanged.connect(self.motion_selected);g.addWidget(self.motion_list)
        self.motion_preview=QLabel("关键帧预览");self.motion_preview.setAlignment(Qt.AlignmentFlag.AlignCenter);self.motion_preview.setMinimumHeight(155);g.addWidget(self.motion_preview)
        self.motion_note=QLabel();self.motion_note.setWordWrap(True);g.addWidget(self.motion_note)
        row=QHBoxLayout();g.addLayout(row);self.button(row,"播放选中动作",self.play_selected_motion);self.button(row,"蓄力 → 扑抓 → 躲闪",self.pet.tease)
        self.motion_group.currentTextChanged.connect(self.render_motions);self.render_motions()
        row=QHBoxLayout();l.addLayout(row);self.mood_demo=QComboBox();self.mood_demo.addItem("跟随真实养成心情",None)
        for mood in MOOD_POOLS:self.mood_demo.addItem(mood,mood)
        row.addWidget(self.mood_demo);self.button(row,"体验情绪动作",self.preview_mood)
        self.motion_current=QLabel();l.addWidget(self.motion_current)
        label=QLabel("后续资源： "+"、".join(PENDING));label.setWordWrap(True);l.addWidget(label)
    def render_motions(self):
        self.motion_ids=[key for key,info in MOTIONS.items() if self.motion_group.currentText()=="全部" or info.group==self.motion_group.currentText()]
        self.motion_list.clear()
        for key in self.motion_ids:
            info=MOTIONS[key];ready=self.pet.art.ensure(info.resource)==info.resource
            self.motion_list.addItem(info.label+(" · 共享姿态变体" if info.note else " · 照片帧")+("" if ready else " [素材不可用]"))
        self.motion_list.setCurrentRow(0)
    def motion_selected(self):
        i=self.motion_list.currentRow()
        if i<0:return
        info=MOTIONS[self.motion_ids[i]]
        frames=self.pet.art.frames.get(info.resource)
        if frames:self.motion_preview.setPixmap(QPixmap.fromImage(frames[min(1,len(frames)-1)]).scaled(280,155,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        self.motion_note.setText(info.note or "独立姿态资源；基于年糕参考照片的 AI 补全，非真实动作录像。")
    def play_selected_motion(self):
        i=self.motion_list.currentRow()
        if i>=0:
            ok=self.pet.perform_action(self.motion_ids[i]);self.notice("正在播放："+MOTIONS[self.motion_ids[i]].label if ok else "该资源未通过加载，不会以静止图冒充")
    def preview_mood(self):
        self.pet.director.override=self.mood_demo.currentData();mood=self.pet.director.mood(self.engine.mood)
        import random
        self.pet.perform_action(random.choice(MOOD_POOLS.get(mood,MOOD_POOLS["平静"])))
        self.notice("情绪动作体验："+mood+"；不修改养成数值")
    def care(self,key,action):
        mapping={"meal":"food_bowl","water":"water_bowl","play":"ball","brush":"brush","bath":"wash_basin","litter":"litter","rest":"bed","checkup":"health_kit"}
        if key in mapping:
            id=mapping[key];uid=next((uid for uid,w in self.pet.desktop.widgets.items() if w.id==id or key=="water" and w.id=="water_fountain"),None)
            if uid is None:
                ok,text=self.pet.desktop.place(id);self.notice(text)
                if not ok:return
                uid=next(uid for uid,w in self.pet.desktop.widgets.items() if w.id==id)
            ok=self.pet.desktop.clean_litter(uid) if key=="litter" else self.pet.desktop.activate(uid);self.notice("年糕正在使用 "+BY_ID[self.pet.desktop.widgets[uid].id]["name"] if ok else "稍等一会儿；空水碗可右键加满")
        else:
            ok,text=self.engine.care(key);self.notice(text)
            if ok:self.pet.pet_head() if key=="pet" else self.pet.perform_action(action)
        self.refresh()
    def shop_page(self,l):
        self.title(l,"年糕的小小补给铺","每件物品都有独立手绘实物图。购买后到背包拖出来，一起布置桌面。")
        self.shop_wallet=QLabel();l.addWidget(self.shop_wallet)
        self.shop_filter=QComboBox();self.shop_filter.addItems(["全部"]+sorted(set(v["category"] for v in BY_ID.values())))
        self.shop_filter.currentTextChanged.connect(self.render_shop);l.addWidget(self.shop_filter)
        self.shop_container=QWidget();self.shop_grid=QGridLayout(self.shop_container);self.shop_grid.setContentsMargins(0,4,0,4);l.addWidget(self.shop_container)
        self.render_shop()
    def clear_grid(self,grid):
        while grid.count():
            item=grid.takeAt(0)
            if item.widget():item.widget().deleteLater()
    def render_shop(self):
        self.clear_grid(self.shop_grid);self.shop_cards={}
        ids=[id for id,v in BY_ID.items() if self.shop_filter.currentText()=="全部" or v["category"]==self.shop_filter.currentText()]
        for i,id in enumerate(ids):
            card=ItemDragCard(id,self.pet,self,"购买",lambda item=id:self.buy_item(item))
            card.button.setEnabled(self.engine.can_buy(id)[0]);card.button.setToolTip(self.engine.can_buy(id)[1]);card.detail.setText(str(BY_ID[id]["price"])+" 金币\n"+("已拥有 "+str(self.engine.data["inventory"].get(id,0)) if BY_ID[id]["ready"] else "待适配 · 不出售"))
            self.shop_grid.addWidget(card,i//3,i%3);self.shop_cards[id]=card
    def buy_item(self,id):
        self.result(self.engine.buy(id));self.render_shop();self.render_backpack()
    def backpack_page(self,l):
        self.title(l,"我的年糕小背包","按住物品图像，拖到生活馆窗口外再松开。只摆放已拥有的物品，Esc 可取消。")
        row=QHBoxLayout();l.addLayout(row);self.clear_desktop_button=self.button(row,"一键清理桌面摆件",self.pet.desktop.clear)
        self.desktop_count=QLabel();row.addWidget(self.desktop_count)
        self.bag_container=QWidget();self.bag_grid=QGridLayout(self.bag_container);self.bag_grid.setContentsMargins(0,4,0,4);l.addWidget(self.bag_container);self.render_backpack()
    def render_backpack(self):
        if not hasattr(self,"bag_grid"):return
        self.clear_grid(self.bag_grid);self.bag_cards={}
        ids=[id for id,n in self.engine.data["inventory"].items() if n>0 and id in BY_ID]
        for i,id in enumerate(ids):
            card=ItemDragCard(id,self.pet,self,"放到桌面" if is_placeable(id) else "使用",lambda item=id:self.place_or_use(item))
            count=self.engine.data["inventory"].get(id,0);available=self.pet.desktop.available(id)
            card.detail.setText("拥有 "+str(count)+" · 可摆 "+str(available))
            card.button.setEnabled(BY_ID[id]["ready"] and (available>0 or not is_placeable(id)))
            self.bag_grid.addWidget(card,i//3,i%3);self.bag_cards[id]=card
        self.desktop_count.setText("桌面已摆 "+str(len(self.pet.desktop.widgets))+" 件")
    def place_or_use(self,id):
        if is_placeable(id):self.result(self.pet.desktop.place(id))
        else:self.result(self.engine.use(id))
        self.render_backpack()
    def refresh_inventory(self):
        if hasattr(self,"bag_grid"):self.render_backpack()
        if hasattr(self,"shop_cards"):
            for id,card in self.shop_cards.items():
                card.button.setEnabled(self.engine.can_buy(id)[0])
        self.refresh()
    def care_objects(self,l):
        group=QGroupBox("把照料用品摆到桌面");g=QGridLayout(group);l.addWidget(group)
        ids=["food_bowl","water_bowl","water_fountain","wand","ball","brush","wash_basin","litter","bed","health_kit"]
        for i,id in enumerate(ids):
            card=ItemDragCard(id,self.pet,self,"摆放",lambda item=id:self.result(self.pet.desktop.place(item)))
            card.detail.setText("拖出可摆放 · 点击实物互动");g.addWidget(card,i//3,i%3)
        self.button(l,"一键清理桌面摆件",self.pet.desktop.clear)
    def focus_page(self,l):
        self.title(l,"一起认真，一起休息","计时依据实际经过时间；退出后暂停，不补发离线专注奖励。")
        self.focus_label=QLabel();self.focus_label.setObjectName("hero");l.addWidget(self.focus_label);row=QHBoxLayout();l.addLayout(row)
        self.button(l,"打开独立专注与待办小窗",self.pet.open_focus)
        self.button(l,"切换工作模式（随机待机）",lambda:self.pet.set_work_mode(not self.pet.work_mode))
        self.minutes=QSpinBox();self.minutes.setRange(1,180);self.minutes.setValue(25);self.minutes.setSuffix(" 分钟");row.addWidget(self.minutes)
        self.button(row,"开始",lambda:self.engine.focus_start(self.minutes.value()));self.button(row,"暂停",self.engine.focus_pause);self.button(row,"继续",self.engine.focus_resume)
        self.tasks=QListWidget();self.tasks.setMinimumHeight(220);self.tasks.itemChanged.connect(self.task_changed);l.addWidget(self.tasks)
        row=QHBoxLayout();l.addLayout(row);self.task_input=QLineEdit();self.task_input.setPlaceholderText("一件今天想完成的小事");row.addWidget(self.task_input);self.button(row,"添加待办",self.add_task)
        self.dday=QDateEdit();self.dday.setCalendarPopup(True);self.dday.setDate(QDate.currentDate());l.addWidget(QLabel("纪念日 / 倒计时"));l.addWidget(self.dday)
        self.button(l,"保存倒计时",lambda:self.set_pref("d_day",self.dday.date().toString("yyyy-MM-dd")));self.dday_label=QLabel();l.addWidget(self.dday_label);self.render_tasks()
    def render_tasks(self):
        self.tasks.blockSignals(True);self.tasks.clear()
        for task in self.engine.data["tasks"][-200:]:
            from PySide6.QtWidgets import QListWidgetItem
            item=QListWidgetItem(task["text"]);item.setData(Qt.ItemDataRole.UserRole,task["id"]);item.setFlags(item.flags()|Qt.ItemFlag.ItemIsUserCheckable);item.setCheckState(Qt.CheckState.Checked if task["done"] else Qt.CheckState.Unchecked)
            if task["done"]:item.setFlags(item.flags()&~Qt.ItemFlag.ItemIsEnabled)
            self.tasks.addItem(item)
        self.tasks.blockSignals(False)
    def task_changed(self,item):
        if item.checkState()==Qt.CheckState.Checked:self.engine.complete_task(item.data(Qt.ItemDataRole.UserRole));self.render_tasks();self.refresh()
    def add_task(self):
        if self.engine.add_task(self.task_input.text()):self.task_input.clear();self.render_tasks()
    def chat_page(self,l):
        self.title(l,"说给年糕听","默认使用本地简短回应。仅主动启用 API 后才发送聊天文字；不读取应用内容或键盘文本。")
        self.chat_log=QTextBrowser();self.chat_log.setMinimumHeight(250);l.addWidget(self.chat_log);self.chat_input=QLineEdit();self.chat_input.setPlaceholderText("今天发生了什么？");self.chat_input.returnPressed.connect(self.send_chat);l.addWidget(self.chat_input)
        self.chat_send=self.button(l,"发送",self.send_chat)
    def send_chat(self):
        text=self.chat_input.text().strip()[:2000]
        if not text:return
        self.chat_input.clear();self.chat_log.append("你："+__import__("html").escape(text))
        if text in ("年糕最可爱","小棕点"):self.engine.unlock_badge("鼻尖小棕点")
        if not self.engine.data["ai"]["enabled"]:
            from ..dialogue import respond
            self.chat_log.append("年糕 [本地回应]："+respond(text));return
        self.chat_send.setEnabled(False);mood=self.engine.mood;history=list(self.history)
        def done(reply):
            self.chat_send.setEnabled(True);self.chat_log.append("年糕 [API]："+__import__("html").escape(reply));self.history.extend([{"role":"user","content":text},{"role":"assistant","content":reply}]);self.history=self.history[-8:];self.calibrate_date()
        def failed(message):self.chat_send.setEnabled(True);self.notice(message);self.chat_log.append("连接失败，可稍后重试；聊天未记入日记。")
        run_job(lambda:self.client.chat(text,mood,history),done,failed)
    def calibrate_date(self):
        if self.engine.data["preferences"]["network_time"] and self.client.server_time:self.engine.calibrate_time(self.client.server_time);self.refresh()
    def diary_page(self,l):
        self.title(l,"猫爪日记","默认仅整理本地游戏事件；AI 日记需单独开启。日记和手写备注都保存在本机。")
        from .calendar_widget import ChineseCalendar
        self.calendar=ChineseCalendar();self.calendar.setMaximumHeight(320);self.calendar.selectionChanged.connect(self.load_diary);l.addWidget(self.calendar)
        self.calendar_info=QLabel();l.addWidget(self.calendar_info)
        self.diary_source=QLabel();l.addWidget(self.diary_source);self.diary_text=QTextEdit();self.diary_text.setMinimumHeight(160);l.addWidget(self.diary_text)
        self.diary_note=QTextEdit();self.diary_note.setPlaceholderText("给今天留一句自己的话");self.diary_note.setMaximumHeight(85);l.addWidget(self.diary_note)
        row=QHBoxLayout();l.addLayout(row);self.button(row,"生成本地日记",self.generate_diary);self.button(row,"生成 AI 日记",self.generate_ai_diary);self.button(row,"保存修改",self.save_diary)
        row=QHBoxLayout();l.addLayout(row);self.button(row,"导出 TXT",lambda:self.export_diary("txt"));self.button(row,"导出 PNG",lambda:self.export_diary("png"));self.load_diary()
    def diary_day(self):return self.calendar.selectedDate().toString("yyyy-MM-dd")
    def load_diary(self):
        from .calendar_cn import china_now,lunar_label
        self.calendar_info.setText(self.diary_day()+" · "+lunar_label(date.fromisoformat(self.diary_day()),True)+"\n中国标准时间 UTC+08:00 · 2020–2069")
        record=self.engine.data["diaries"].get(self.diary_day(),{});self.diary_text.setPlainText(record.get("text",""));self.diary_note.setPlainText(record.get("note",""));self.diary_source.setText(record.get("source","这一天还没有日记"))
    def generate_diary(self):self.engine.local_diary(self.diary_day());self.load_diary();self.notice("已根据实际游戏事件生成")
    def save_diary(self):
        day=self.diary_day();old=self.engine.data["diaries"].get(day,{})
        self.engine.data["diaries"][day]=dict(text=self.diary_text.toPlainText()[:20000],note=self.diary_note.toPlainText()[:10000],source=old.get("source","手动记录"));self.engine.save();self.notice("日记已保存")
    def generate_ai_diary(self):
        if not self.engine.data["ai"]["enabled"] or not self.engine.data["ai"]["diary_enabled"]:return self.notice("请在设置中分别启用联网 AI 和 AI 日记")
        day=self.diary_day();events=[dict(e) for e in self.engine.data["events"] if e["day"]==day];mood=self.engine.mood;self.notice("正在整理已记录的游戏事件…")
        def done(text):
            old=self.engine.data["diaries"].get(day,{});self.engine.data["diaries"][day]=dict(text=text,note=old.get("note",""),source="联网 AI · 根据本地游戏事件");self.engine.save();self.load_diary();self.calibrate_date();self.notice("AI 日记已保存")
        run_job(lambda:self.client.diary(events,mood),done,self.notice)
    def export_diary(self,kind):
        self.save_diary();path,_=QFileDialog.getSaveFileName(self,"导出日记","年糕日记-"+self.diary_day()+"."+kind,"Text (*.txt)" if kind=="txt" else "PNG (*.png)")
        if not path:return
        text=self.diary_day()+" 年糕日记\n\n"+self.diary_text.toPlainText()+"\n\n"+self.diary_note.toPlainText()
        try:
            if kind=="txt":Path(path).write_text(text,encoding="utf-8")
            else:
                from PySide6.QtGui import QTextDocument,QImage
                doc=QTextDocument();doc.setDefaultFont(self.font());doc.setPlainText(text);doc.setTextWidth(720)
                image=QImage(800,max(350,int(doc.size().height())+100),QImage.Format.Format_ARGB32);image.fill(QColor("#EFF6F1"));p=QPainter(image);p.translate(40,40);doc.drawContents(p);p.end()
                if not image.save(path):raise OSError("PNG 写入失败")
            self.notice("导出完成："+path)
        except OSError as exc:self.notice(str(exc))
    def set_pref(self,key,value):self.engine.data["preferences"][key]=value;self.engine.save()
    def settings_page(self,l):
        self.title(l,"只为你和年糕","数据保存在用户目录。默认不联网、不监听全局键盘、不自动启动。")
        group=QGroupBox("年糕的性格与习惯 · 每次 API 请求强制读取");form=QFormLayout(group);l.addWidget(group);self.profile_fields={}
        profile=sanitize_profile(self.engine.data["profile"])
        for key,label in [("personality","性格"),("habits","日常习惯"),("likes","喜欢什么"),("dislikes","不喜欢什么"),("speaking_style","说话风格"),("owner_name","主人的称呼"),("notes","其他真实观察")]:
            field=QTextEdit() if key in ("personality","habits","notes") else QLineEdit()
            if isinstance(field,QTextEdit):field.setMaximumHeight(82);field.setPlainText(profile[key])
            else:field.setText(profile[key])
            field.setPlaceholderText("可留空；未填写的内容不会假装已知");form.addRow(label,field);self.profile_fields[key]=field
        self.button(form,"保存年糕档案",self.save_profile)
        note=QLabel("聊天与 AI 日记每次联网前都重新读取档案、生日计算的真实年龄和当前状态；换 Key 也不能跳过。留空会标记未知。");note.setWordWrap(True);form.addRow(note)
        self.title(l,"生日与体验年龄")
        self.birth=QDateEdit(QDate.fromString(self.engine.data["birth_date"],"yyyy-MM-dd"));self.birth.setCalendarPopup(True);self.birth.setMaximumDate(QDate.currentDate());l.addWidget(self.birth)
        self.button(l,"保存生日",self.save_birth);self.button(l,"恢复真实年龄",self.reset_age)
        form=QFormLayout();l.addLayout(form);activity=QSpinBox();activity.setRange(0,100);activity.setValue(self.engine.data["preferences"]["activity"]);activity.valueChanged.connect(lambda v:self.set_pref("activity",v));form.addRow("活动频率",activity)
        opacity=QSpinBox();opacity.setRange(30,100);opacity.setValue(100);opacity.valueChanged.connect(lambda v:self.pet.setWindowOpacity(v/100));form.addRow("桌宠不透明度 %",opacity)
        for key,label in [("easter_eggs","允许彩蛋"),("network_time","用 AI 服务 HTTP 日期校准生日计算（失败用本机日期）")]:
            b=QCheckBox(label);b.setChecked(self.engine.data["preferences"][key]);b.toggled.connect(lambda v,k=key:self.set_pref(k,v));l.addWidget(b)
        self.button(l,"切换桌宠置顶",self.pet.toggle_top);self.button(l,"导入自定义透明 PNG（单姿态）",self.import_png)
        sound_group=QGroupBox("动作联动与音效");sound_layout=QVBoxLayout(sound_group);l.addWidget(sound_group)
        for key,label in [("emotion_actions","根据心情自主播放动作"),("cursor_chase","允许追逐 / 蹲守光标（不捕获或移动系统鼠标）"),
                          ("input_link","允许打字联动：仅检测按键活动，不记录文字（Windows）"),("sound","启用合成示意音效（不是年糕真实录音）")]:
            check=QCheckBox(label);check.setChecked(self.engine.data["preferences"][key]);check.toggled.connect(lambda value,k=key:self.interaction_pref(k,value));sound_layout.addWidget(check)
        volume=QSpinBox();volume.setRange(0,100);volume.setValue(self.engine.data["preferences"]["volume"]);volume.setSuffix(" % 音效音量")
        volume.valueChanged.connect(lambda value:self.interaction_pref("volume",value));sound_layout.addWidget(volume)
        row=QHBoxLayout();sound_layout.addLayout(row);self.sound_choice=ClickSelectComboBox()
        for key,label in SOUNDS.items():self.sound_choice.addItem(label,key)
        row.addWidget(self.sound_choice);self.button(row,"试听已选音效",self.preview_sound);self.button(row,"立即停止音效",self.pet.audio.stop)
        label=QLabel("仅检测是否按键，不安装键盘钩子、不读取屏幕内容。声音在本机合成，可随时静音。系统音量通知、联网天气与开机启动仍未接入。");label.setWordWrap(True);sound_layout.addWidget(label)
        group=QGroupBox("可选联网 AI · 多平台协议适配");f=QFormLayout(group);l.addWidget(group)
        self.ai_enabled=QCheckBox("允许发送聊天文字及年糕档案");self.ai_enabled.setChecked(self.engine.data["ai"]["enabled"]);f.addRow(self.ai_enabled)
        self.ai_diary=QCheckBox("另行允许发送游戏事件及年糕档案用于 AI 日记");self.ai_diary.setChecked(self.engine.data["ai"]["diary_enabled"]);f.addRow(self.ai_diary)
        from .providers import PRESETS,PROTOCOLS
        self.api_presets=ClickSelectComboBox()
        for name,*_ in PRESETS:self.api_presets.addItem(name)
        f.addRow("平台预设",self.api_presets)
        self.api_protocol=ClickSelectComboBox()
        for key,label in PROTOCOLS.items():self.api_protocol.addItem(label,key)
        self.api_protocol.setCurrentIndex(max(0,self.api_protocol.findData(self.engine.data["ai"]["protocol"])));f.addRow("接口协议",self.api_protocol)
        self.base_url=QLineEdit(self.engine.data["ai"]["base_url"]);f.addRow("API 地址",self.base_url);self.model=QLineEdit(self.engine.data["ai"]["model"]);f.addRow("模型",self.model)
        self.api_presets.activated.connect(self.apply_api_preset)
        self.api_tokens=QSpinBox();self.api_tokens.setRange(64,16384);self.api_tokens.setValue(self.engine.data["ai"]["max_tokens"]);f.addRow("输出预算上限",self.api_tokens)
        self.api_timeout=QSpinBox();self.api_timeout.setRange(10,180);self.api_timeout.setSuffix(" 秒");self.api_timeout.setValue(self.engine.data["ai"]["timeout"]);f.addRow("请求超时",self.api_timeout)
        hint=QLabel("模型 ID 以服务商控制台为准；预设不代表所有账户可用。支持基础地址或完整接口地址。思考模型自动增加预算，连接测试也可能产生少量费用。");hint.setWordWrap(True);f.addRow(hint)
        self.key=QLineEdit();self.key.setEchoMode(QLineEdit.EchoMode.Password);self.key.setPlaceholderText("留空保留旧密钥；Windows 使用当前用户 DPAPI 加密");f.addRow("API Key",self.key)
        self.button(f,"保存 API 配置",self.save_ai);self.button(f,"删除密钥",lambda:(self.vault.clear(),self.notice("密钥已删除")))
        self.api_test_button=self.button(f,"保存并测试连接",self.test_api_connection)
        self.api_result=QLabel("密钥仅在本机填写，不要发送到聊天窗口。");self.api_result.setWordWrap(True);f.addRow(self.api_result)
        note=QLabel("未完成：服饰绑定、真实照片重建、幼年/老年独立模型、复杂家具攀爬、Live2D、移动端。默认照片动作由参考图 AI 补全；请以照片为长相依据。");note.setWordWrap(True);l.addWidget(note)
    def interaction_pref(self,key,value):
        self.set_pref(key,value)
        if (key=="sound" and not value) or (key=="volume" and value==0):self.pet.audio.stop()
        if key=="cursor_chase" and not value:self.pet.cursor_target=None;self.pet.cursor_mode=False
        if key=="input_link" and value and not self.pet.keyboard.supported:self.notice("全局打字联动需要 Windows；当前平台仅可手动预览动作")
    def preview_sound(self):
        ok=self.pet.audio.play(self.sound_choice.currentData(),True)
        self.notice("正在试听合成音效" if ok else "请先开启声音并调高音量；自动播放需要 Windows 音频设备")
    def save_profile(self):
        values={key:(field.toPlainText() if isinstance(field,QTextEdit) else field.text()) for key,field in self.profile_fields.items()}
        self.engine.data["profile"]=sanitize_profile(dict(self.engine.data["profile"],**values))
        self.engine.save();self.history.clear();self.notice("性格习惯已保存；每次 API 回复前都会重新读取")
    def save_birth(self):self.engine.data["birth_date"]=self.birth.date().toString("yyyy-MM-dd");self.engine.save();self.refresh();self.notice("生日已更新")
    def reset_age(self):self.engine.data["age_override"]=None;self.engine.data["age_frozen"]=False;self.engine.save();self.refresh()
    def apply_api_preset(self,index):
        from .providers import PRESETS
        _,protocol,base,model=PRESETS[index]
        self.api_protocol.setCurrentIndex(self.api_protocol.findData(protocol))
        if base:self.base_url.setText(base)
        self.model.setText(model);self.model.setPlaceholderText("填写此账户控制台可用的模型 / endpoint ID")
        self.key.clear()
        from urllib.parse import urlsplit
        self.api_platform_changed=bool(base and urlsplit(base).hostname!=urlsplit(self.engine.data["ai"]["base_url"]).hostname)
        self.api_result.setText("已选择平台预设；旧配置尚未改动。请填写对应密钥后保存。")
    def test_api_connection(self):
        if not self.save_ai():return
        client=AIClient(dict(self.engine.data["ai"],enabled=True),self.vault,self.engine.profile_snapshot)
        self.api_test_button.setEnabled(False);self.api_result.setText("正在向所填地址发送一条测试消息和年糕档案…")
        def done(reply):self.api_test_button.setEnabled(True);self.api_result.setText(reply)
        def failed(error):self.api_test_button.setEnabled(True);self.api_result.setText("连接失败："+error)
        run_job(client.test_connection,done,failed)
    def save_ai(self):
        try:
            self.save_profile();self.engine.profile_snapshot()
            base=checked_base(self.base_url.text())
            if not self.model.text().strip():raise ValueError("模型名不能为空")
            if len(self.model.text().strip())>200:raise ValueError("模型 ID 过长，请填写控制台的模型标识")
            from urllib.parse import urlsplit
            changed_host=urlsplit(base).hostname!=urlsplit(self.engine.data["ai"]["base_url"]).hostname
            if (changed_host or getattr(self,"api_platform_changed",False)) and not self.key.text().strip():raise ValueError("切换平台或服务地址后，请重新填写对应平台的密钥，避免误用旧 Key")
            if self.key.text().strip():self.vault.save(self.key.text());self.key.clear()
            self.api_platform_changed=False
            self.engine.data["ai"].update(enabled=self.ai_enabled.isChecked(),diary_enabled=self.ai_diary.isChecked(),base_url=base,model=self.model.text().strip()[:200],protocol=self.api_protocol.currentData(),max_tokens=self.api_tokens.value(),timeout=self.api_timeout.value());self.engine.save();self.notice("API 配置已保存；密钥不写入普通 JSON");return True
        except (ValueError,OSError) as exc:self.notice(str(exc));return False
    def import_png(self):
        path,_=QFileDialog.getOpenFileName(self,"选择透明 PNG","","PNG (*.png)")
        if not path:return
        from PySide6.QtGui import QImage
        image=QImage(path)
        if image.isNull() or not image.hasAlphaChannel() or image.width()>4096 or image.height()>4096:return self.notice("需要带透明通道、尺寸不超过 4096×4096 的 PNG")
        try:
            from ..art import alpha_bounds
            image=image.copy(alpha_bounds(image))
            dest=self.engine.path.parent/"custom.png";image.save(str(dest));self.pet.art.frames["custom"]=[image];self.pet.perform_action("custom",30);self.notice("已导入单姿态，展示 30 秒；不会覆盖年糕原图")
        except (ValueError,OSError) as exc:self.notice(str(exc))
    def refresh(self):
        from .calendar_cn import china_now
        self.clock_label.setText(china_now().strftime("%Y.%m.%d  %A  %H:%M").replace("Monday","星期一").replace("Tuesday","星期二").replace("Wednesday","星期三").replace("Thursday","星期四").replace("Friday","星期五").replace("Saturday","星期六").replace("Sunday","星期日"))
        rows=self.pet.desktop.status_rows();self.desktop_status.setText("\n".join(rows) if rows else "桌面还空着，把一只粮碗或猫砂盆从背包拖出来吧。")
        self.motion_current.setText("当前动作："+MOTIONS.get(self.pet.work_pose if self.pet.work_mode else self.pet.behaviour.state,MOTIONS["idle"]).label+"  ·  体验情绪："+self.pet.director.mood(self.engine.mood))
        e=self.engine;a=e.age();self.age_label.setText("年糕 NIANGAO · 布偶猫 · 男孩子\n"+a["text"]+" · "+a["stage"]+" · 约人类 "+str(a["human_years"])+" 岁"+("\n体验年龄已冻结，真实生日仍保留" if e.data["age_frozen"] else ""))
        self.summary.setText(f'Lv.{e.level}  ·  经验 {e.data["xp"]}  ·  金币 {e.data["coins"]}  ·  心情 {e.mood}')
        for key,bar in self.bars.items():bar.setValue(round(e.data["stats"][key]))
        self.curve.update();lines=[v["at"][11:16]+"  "+v["text"] for v in e.data["events"][-6:]]
        if e.data["postcards"]:lines.append("明信片："+ "、".join(v["place"] for v in e.data["postcards"][-4:]))
        if e.data["badges"]:lines.append("徽章："+ "、".join(e.data["badges"]))
        self.events.setPlainText("\n".join(lines) or "从一次轻轻摸头开始，留下今天的第一条记录。")
        seconds=e.data["focus"]["remaining"];self.focus_label.setText(f'{seconds//60:02d}:{seconds%60:02d}'+("  专注中" if e.data["focus"]["active"] else "  已暂停"))
        day=e.data["preferences"]["d_day"]
        if day:
            try:self.dday_label.setText("距 "+day+"："+str((date.fromisoformat(day)-e.today()).days)+" 天")
            except ValueError:self.dday_label.setText("倒计时日期无效")
        if hasattr(self,"shop_wallet"):self.shop_wallet.setText("小鱼干基金："+str(self.engine.data["coins"])+" 金币")
        if hasattr(self,"desktop_count"):self.desktop_count.setText("桌面已摆 "+str(len(self.pet.desktop.widgets))+" 件")
        if hasattr(self,"shop_cards"):
            for id,card in self.shop_cards.items():card.button.setEnabled(self.engine.can_buy(id)[0])
    def changeEvent(self,event):
        super().changeEvent(event)
        if event.type()==QEvent.Type.ActivationChange and hasattr(self,"pet"):
            from ..desktop_focus import prioritize_dashboard
            prioritize_dashboard(self,self.isActiveWindow())
    def closeEvent(self,event):
        from ..desktop_focus import prioritize_dashboard
        prioritize_dashboard(self,False);self.engine.save();event.ignore();self.hide()
    def shutdown(self):
        self.timer.stop()
        self.hide()
