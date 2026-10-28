"""Local-first multifunction dashboard. The desktop pet remains a separate window."""
import json,uuid,sys
from pathlib import Path
from datetime import date
from PySide6.QtCore import Qt,QTimer,QDate
from PySide6.QtGui import QPixmap,QPainter,QColor
from PySide6.QtWidgets import (QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,
    QListWidget,QStackedWidget,QScrollArea,QProgressBar,QComboBox,QSpinBox,QDoubleSpinBox,QTextBrowser,
    QLineEdit,QTextEdit,QCheckBox,QCalendarWidget,QFileDialog,QDateEdit,QGroupBox,QFormLayout)
from ..art import asset_path
from .engine import STAT_NAMES
from .catalog import BY_ID,SCENES
from .ai import SecretVault,AIClient,checked_base
from .jobs import run_job
STYLE="""
QMainWindow,QWidget {background:#EFF6F1;color:#305E63;font-size:14px;}
QLabel#hero {font-size:28px;font-weight:700;} QLabel#sub {color:#698478;}
QPushButton {background:#40A387;color:white;border:0;border-radius:8px;padding:10px 16px;}
QPushButton:hover {background:#305E63;} QPushButton:disabled {background:#cdd9d0;color:#6c8278;}
QLineEdit,QTextEdit,QTextBrowser,QSpinBox,QDoubleSpinBox,QComboBox,QDateEdit {background:white;border:1px solid #b5d7cd;border-radius:6px;padding:7px;}
QListWidget {background:#305E63;color:#EFF6F1;border:0;border-radius:12px;padding:8px;}
QListWidget::item {padding:15px 10px;margin:3px;} QListWidget::item:selected {background:#40A387;border-radius:8px;}
QGroupBox {border:1px solid #b5d7cd;border-radius:10px;margin-top:14px;padding:14px;}
QGroupBox::title {subcontrol-origin:margin;left:15px;padding:0 5px;}
QProgressBar {border:0;background:#dbe6df;border-radius:6px;min-height:19px;text-align:center;}
QProgressBar::chunk {background:#8CCCCA;border-radius:6px;}
QCheckBox {padding:5px;} QScrollArea {border:0;}
"""
from ..interaction.actions import ACTIONS as MOTIONS,MOOD_POOLS,SOUNDS
ACTIONS={key:info.label for key,info in MOTIONS.items()}
PENDING=["跳上真实家具","攀爬猫树","服饰穿戴","幼猫/老年独立模型","完整 3D 骨骼走跑"]
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
        super().__init__();self.pet=pet;self.engine=pet.life;self.home=None;self.setWindowTitle("年糕生活馆 · NIANGAO");self.resize(1100,780);self.setMinimumSize(880,620);self.setStyleSheet(STYLE)
        self.vault=SecretVault(self.engine.path.parent/"api-key.dpapi");self.client=AIClient(self.engine.data["ai"],self.vault);self.history=[]
        base=QWidget();self.setCentralWidget(base);outer=QVBoxLayout(base);row=QHBoxLayout();outer.addLayout(row)
        self.nav=QListWidget();self.nav.setFixedWidth(180);self.stack=QStackedWidget();row.addWidget(self.nav);row.addWidget(self.stack,1)
        self.status=QLabel("本地保存 · 年糕的照片形象始终保留");self.status.setWordWrap(True);outer.addWidget(self.status)
        builders=[("陪伴总览",self.overview),("照料与动作",self.care_page),("3D 小家",self.home_page),("商城与背包",self.shop_page),
                  ("专注与待办",self.focus_page),("和年糕聊天",self.chat_page),("年糕日记",self.diary_page),("设置与图鉴",self.settings_page)]
        for name,builder in builders:
            self.nav.addItem(name);page=QWidget();layout=QVBoxLayout(page);builder(layout);layout.addStretch()
            scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(page);self.stack.addWidget(scroll)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex);self.nav.setCurrentRow(0)
        self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(1000);self.refresh()
    def title(self,layout,title,subtitle=""):
        label=QLabel(title);label.setObjectName("hero");layout.addWidget(label)
        if subtitle:
            label=QLabel(subtitle);label.setObjectName("sub");label.setWordWrap(True);layout.addWidget(label)
    def button(self,layout,text,callback):
        b=QPushButton(text);b.clicked.connect(lambda _checked=False:callback());layout.addWidget(b);return b
    def notice(self,text):self.status.setText(str(text))
    def result(self,result):self.notice(result[1]);self.refresh()
    def overview(self,l):
        self.title(l,"你好，今天也有年糕陪你","真实生日 · 照料记录 · 小小的陪伴奖励")
        row=QHBoxLayout();l.addLayout(row);photo=QLabel();photo.setPixmap(QPixmap(str(asset_path("niangao-idle.png"))).scaled(190,230,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation));row.addWidget(photo)
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
        group=QGroupBox("动作与表情图鉴 · 照片关键帧");g=QVBoxLayout(group);l.addWidget(group)
        label=QLabel("轻点：摸头；按住约 0.85 秒：轻啃指尖；左键拖拽：抱起；Shift + 左键滑动：抚摸；双击：戳一下。\n四帧照片补全不是完整 3D 骨骼动画，较大变姿仍有跳变。");label.setWordWrap(True);g.addWidget(label)
        self.motion_group=QComboBox();self.motion_group.addItems(["全部"]+sorted(set(info.group for info in MOTIONS.values())));g.addWidget(self.motion_group)
        self.motion_list=QListWidget();self.motion_list.setMinimumHeight(260);self.motion_list.currentRowChanged.connect(self.motion_selected);g.addWidget(self.motion_list)
        self.motion_preview=QLabel("关键帧预览");self.motion_preview.setAlignment(Qt.AlignmentFlag.AlignCenter);self.motion_preview.setMinimumHeight(210);g.addWidget(self.motion_preview)
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
        if frames:self.motion_preview.setPixmap(QPixmap.fromImage(frames[min(1,len(frames)-1)]).scaled(340,210,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
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
        ok,text=self.engine.care(key);self.notice(text)
        if ok:
            if key=="meal":self.pet.feed()
            elif key=="pet":self.pet.pet_head()
            elif key=="play":self.pet.tease()
            else:self.pet.perform_action(action)
            self.pet.bubble.speak(text,self.pet.rect_global(),self.pet.areas())
        self.refresh()
    def home_page(self,l):
        self.title(l,"年糕的 3D 小家 · 实验版","照片桌宠保持原样。这里是程序建模的实验猫，不是照片扫描复原；有方向的毛束不是最终真实长毛。")
        row=QHBoxLayout();l.addLayout(row);self.scene_combo=QComboBox()
        for key,name in SCENES.items():self.scene_combo.addItem(name,key)
        self.scene_combo.setCurrentIndex(self.scene_combo.findData(self.engine.data["scene"]));row.addWidget(self.scene_combo)
        self.button(row,"进入空间",self.change_scene);self.button(row,"启动实时 3D",self.start_home)
        self.home_host=QVBoxLayout();l.addLayout(self.home_host);self.preview=QLabel();self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setPixmap(QPixmap(str(asset_path("models/niangao-3d-preview.png"))).scaled(430,430,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation));self.home_host.addWidget(self.preview)
        self.furniture=QComboBox();l.addWidget(self.furniture);self.update_furniture()
        row=QHBoxLayout();l.addLayout(row);self.button(row,"摆放背包家具",self.place_furniture);self.button(row,"删除选中家具",self.remove_furniture);self.button(row,"镜头看年糕",lambda:self.home.focus_cat() if self.home else self.notice("请先启动实时 3D"))
        self.placed=QComboBox();self.placed.currentIndexChanged.connect(self.select_furniture);l.addWidget(self.placed)
        row=QHBoxLayout();l.addLayout(row);self.rotation=QSpinBox();self.rotation.setRange(0,359);self.rotation.setSuffix("°");row.addWidget(QLabel("旋转"));row.addWidget(self.rotation)
        self.scale=QDoubleSpinBox();self.scale.setRange(.5,1.8);self.scale.setSingleStep(.1);self.scale.setValue(1);row.addWidget(QLabel("缩放"));row.addWidget(self.scale)
        self.button(row,"应用变换",self.transform_furniture)
        self.place_mode=QCheckBox("摆放模式：拖动选中家具；0.25 米网格吸附，阻止家具重叠与侵入猫咪保留区");self.place_mode.toggled.connect(self.placement_mode);l.addWidget(self.place_mode)
        row=QHBoxLayout();l.addLayout(row);self.preset=QLineEdit();self.preset.setPlaceholderText("布局名称");row.addWidget(self.preset)
        self.button(row,"保存布局",self.save_layout);self.button(row,"恢复布局",self.load_layout);self.update_placed()
    def change_scene(self):
        ok,text=self.engine.set_scene(self.scene_combo.currentData());self.notice(text)
        if ok:
            if self.home:self.home.rebuild()
            self.update_placed()
    def start_home(self):
        if self.home:return
        try:
            from .home3d import Home3D
            self.home=Home3D(self.engine,self.notice);self.preview.hide();self.home_host.addWidget(self.home);self.notice("实时 3D 已启动；鼠标左键环绕，滚轮缩放。模型未绑定完整骨骼。")
        except Exception as exc:self.notice("实时 3D 不可用，保留静态渲染预览："+str(exc)[:180])
    def update_furniture(self):
        self.furniture.clear()
        for id,count in self.engine.data["inventory"].items():
            if count and id in BY_ID and BY_ID[id]["kind"]=="furniture":self.furniture.addItem(BY_ID[id]["name"]+" ×"+str(count),id)
    def update_placed(self):
        self.placed.clear()
        for it in self.engine.data["layouts"].get(self.engine.data["scene"],[]):self.placed.addItem(BY_ID[it["type"]]["name"],it["id"])
    def select_furniture(self):
        id=self.placed.currentData()
        if self.home:self.home.selected=id
        for it in self.engine.data["layouts"].get(self.engine.data["scene"],[]):
            if it["id"]==id:self.rotation.setValue(int(it.get("rotation",0)));self.scale.setValue(it.get("scale",1))
    def placement_mode(self,value):
        if self.home:self.home.placement=value;self.home.orbit.setEnabled(not value)
    def place_furniture(self):
        from .layout import valid_placement
        id=self.furniture.currentData()
        if not id:return
        items=self.engine.data["layouts"].setdefault(self.engine.data["scene"],[])
        if sum(it["type"]==id for it in items)>=self.engine.data["inventory"].get(id,0):return self.notice("这件家具已经全部摆放")
        for x,z in [(x/2,z/2) for x in range(-6,7) for z in range(-6,7)]:
            it=dict(id=uuid.uuid4().hex,type=id,x=x,z=z,rotation=0,scale=1)
            obstacles=self.home.builtin_obstacles() if self.home else self.builtin_obstacles()
            if valid_placement(it,items+obstacles)[0]:
                items.append(it);self.engine.save()
                if self.home:self.home.add_entity(it)
                self.update_placed();self.placed.setCurrentIndex(self.placed.count()-1);return self.notice("家具已放入房间；开启摆放模式可拖动")
        self.notice("没有足够空地，请移除部分家具")
    def builtin_obstacles(self):
        scene=self.engine.data["scene"]
        return [dict(id="builtin",type="builtin",x=0 if scene=="kitchen" else -1.8,z=-2.6,scale=2.05 if scene=="kitchen" else 1,rotation=0)] if scene in ("desk","living","bedroom","kitchen") else []
    def remove_furniture(self):
        items=self.engine.data["layouts"].get(self.engine.data["scene"],[]);id=self.placed.currentData()
        items[:]=[it for it in items if it["id"]!=id];self.engine.save()
        if self.home:self.home.rebuild()
        self.update_placed()
    def transform_furniture(self):
        from .layout import valid_placement
        items=self.engine.data["layouts"].get(self.engine.data["scene"],[])
        for i,it in enumerate(items):
            if it["id"]==self.placed.currentData():
                candidate=dict(it,rotation=self.rotation.value(),scale=self.scale.value());ok,text=valid_placement(candidate,items+self.builtin_obstacles())
                if ok:
                    if self.home:self.home.move_item(candidate)
                    else:items[i]=candidate
                    self.engine.save();self.notice("变换已保存")
                else:self.notice(text)
    def save_layout(self):
        name=self.preset.text().strip()[:40]
        if not name:return self.notice("请填写布局名称")
        import copy
        self.engine.data["layout_presets"][name]={"scene":self.engine.data["scene"],"items":copy.deepcopy(self.engine.data["layouts"].get(self.engine.data["scene"],[]))}
        self.engine.save();self.notice("布局已保存")
    def load_layout(self):
        import copy
        record=self.engine.data["layout_presets"].get(self.preset.text().strip())
        if not record or record["scene"]!=self.engine.data["scene"]:return self.notice("当前空间没有这个布局")
        from .layout import valid_placement
        good=[]
        for item in record["items"]:
            try:
                if not valid_placement(item,good+self.builtin_obstacles())[0]:return self.notice("布局存在家具重叠，未恢复")
                if sum(it["type"]==item["type"] for it in good)>=self.engine.data["inventory"].get(item["type"],0):return self.notice("背包家具不足，未恢复")
                good.append(copy.deepcopy(item))
            except (KeyError,TypeError,ValueError):return self.notice("布局文件损坏，未恢复")
        self.engine.data["layouts"][record["scene"]]=good;self.engine.save()
        if self.home:self.home.rebuild()
        self.update_placed();self.notice("布局已恢复")
    def shop_page(self,l):
        self.title(l,"小鱼干补给站","金币只存在本地游戏内，不涉及真实付款。未完成服饰绑定的商品不可购买。")
        self.shop_filter=QComboBox();self.shop_filter.addItems(["全部"]+sorted(set(it["category"] for it in BY_ID.values())));self.shop_filter.currentTextChanged.connect(self.render_shop);l.addWidget(self.shop_filter)
        self.shop_list=QListWidget();self.shop_list.setMinimumHeight(350);self.shop_list.currentRowChanged.connect(self.shop_selection);l.addWidget(self.shop_list)
        self.shop_info=QLabel();self.shop_info.setWordWrap(True);l.addWidget(self.shop_info);row=QHBoxLayout();l.addLayout(row)
        self.buy_button=self.button(row,"购买",self.buy_item);self.use_button=self.button(row,"使用背包物品",self.use_item);self.render_shop()
    def render_shop(self):
        self.shop_ids=[id for id,it in BY_ID.items() if self.shop_filter.currentText()=="全部" or it["category"]==self.shop_filter.currentText()]
        self.shop_list.clear()
        for id in self.shop_ids:
            it=BY_ID[id];self.shop_list.addItem(f'{it["name"]}   ·   {it["price"]} 金币   ·   背包 {self.engine.data["inventory"].get(id,0)}'+("   [待适配]" if not it["ready"] else ""))
        self.shop_list.setCurrentRow(0)
    def shop_selection(self):
        row=self.shop_list.currentRow()
        if row<0 or row>=len(self.shop_ids):return
        id=self.shop_ids[row];it=BY_ID[id];ok,reason=self.engine.can_buy(id)
        self.shop_info.setText(it["note"] or reason or "已准备，可购买");self.buy_button.setEnabled(ok);self.use_button.setEnabled(it["ready"] and self.engine.data["inventory"].get(id,0)>0)
    def buy_item(self):
        row=self.shop_list.currentRow()
        if row>=0:self.result(self.engine.buy(self.shop_ids[row]));self.render_shop();self.update_furniture()
    def use_item(self):
        row=self.shop_list.currentRow()
        if row<0:return
        id=self.shop_ids[row];ok,text=self.engine.use(id);self.notice(text)
        if ok:
            kind=BY_ID[id]["kind"]
            if kind=="consumable":self.pet.perform_action("feed")
            elif kind=="toy":self.pet.director.sequence([("chew_toy",3),("swat",2.5)],self.pet.play_step)
            elif kind=="room":
                self.scene_combo.setCurrentIndex(self.scene_combo.findData(self.engine.data["scene"]))
                if self.home:self.home.rebuild()
                self.update_placed()
        self.render_shop();self.refresh()
    def focus_page(self,l):
        self.title(l,"一起认真，一起休息","计时依据实际经过时间；退出后暂停，不补发离线专注奖励。")
        self.focus_label=QLabel();self.focus_label.setObjectName("hero");l.addWidget(self.focus_label);row=QHBoxLayout();l.addLayout(row)
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
        self.chat_log=QTextBrowser();self.chat_log.setMinimumHeight(370);l.addWidget(self.chat_log);self.chat_input=QLineEdit();self.chat_input.setPlaceholderText("今天发生了什么？");self.chat_input.returnPressed.connect(self.send_chat);l.addWidget(self.chat_input)
        self.chat_send=self.button(l,"发送",self.send_chat)
    def send_chat(self):
        text=self.chat_input.text().strip()[:2000]
        if not text:return
        self.chat_input.clear();self.chat_log.append("你："+__import__("html").escape(text))
        if text in ("年糕最可爱","小棕点"):self.engine.unlock_badge("鼻尖小棕点")
        if not self.engine.data["ai"]["enabled"]:self.chat_log.append("年糕 [本地回应]：喵～我在这里陪你。先摸摸我的小脑袋，再喝一口水吧。");return
        self.chat_send.setEnabled(False);mood=self.engine.mood;history=list(self.history)
        def done(reply):
            self.chat_send.setEnabled(True);self.chat_log.append("年糕 [API]："+__import__("html").escape(reply));self.history.extend([{"role":"user","content":text},{"role":"assistant","content":reply}]);self.history=self.history[-8:];self.calibrate_date()
        def failed(message):self.chat_send.setEnabled(True);self.notice(message);self.chat_log.append("连接失败，可稍后重试；聊天未记入日记。")
        run_job(lambda:self.client.chat(text,mood,history),done,failed)
    def calibrate_date(self):
        if self.engine.data["preferences"]["network_time"] and self.client.server_date:self.engine.network_today=self.client.server_date;self.refresh()
    def diary_page(self,l):
        self.title(l,"猫爪日记","默认仅整理本地游戏事件；AI 日记需单独开启。日记和手写备注都保存在本机。")
        self.calendar=QCalendarWidget();self.calendar.setMaximumHeight(240);self.calendar.selectionChanged.connect(self.load_diary);l.addWidget(self.calendar)
        self.diary_source=QLabel();l.addWidget(self.diary_source);self.diary_text=QTextEdit();self.diary_text.setMinimumHeight(160);l.addWidget(self.diary_text)
        self.diary_note=QTextEdit();self.diary_note.setPlaceholderText("给今天留一句自己的话");self.diary_note.setMaximumHeight(85);l.addWidget(self.diary_note)
        row=QHBoxLayout();l.addLayout(row);self.button(row,"生成本地日记",self.generate_diary);self.button(row,"生成 AI 日记",self.generate_ai_diary);self.button(row,"保存修改",self.save_diary)
        row=QHBoxLayout();l.addLayout(row);self.button(row,"导出 TXT",lambda:self.export_diary("txt"));self.button(row,"导出 PNG",lambda:self.export_diary("png"));self.load_diary()
    def diary_day(self):return self.calendar.selectedDate().toString("yyyy-MM-dd")
    def load_diary(self):
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
        row=QHBoxLayout();sound_layout.addLayout(row);self.sound_choice=QComboBox()
        for key,label in SOUNDS.items():self.sound_choice.addItem(label,key)
        row.addWidget(self.sound_choice);self.button(row,"试听已选音效",self.preview_sound);self.button(row,"立即停止音效",self.pet.audio.stop)
        label=QLabel("仅检测是否按键，不安装键盘钩子、不读取屏幕内容。声音在本机合成，可随时静音。系统音量通知、联网天气与开机启动仍未接入。");label.setWordWrap(True);sound_layout.addWidget(label)
        group=QGroupBox("可选联网 AI · OpenAI 兼容接口");f=QFormLayout(group);l.addWidget(group)
        self.ai_enabled=QCheckBox("允许发送主动输入的聊天文字");self.ai_enabled.setChecked(self.engine.data["ai"]["enabled"]);f.addRow(self.ai_enabled)
        self.ai_diary=QCheckBox("另行允许发送游戏事件用于 AI 日记");self.ai_diary.setChecked(self.engine.data["ai"]["diary_enabled"]);f.addRow(self.ai_diary)
        self.base_url=QLineEdit(self.engine.data["ai"]["base_url"]);f.addRow("API 地址",self.base_url);self.model=QLineEdit(self.engine.data["ai"]["model"]);f.addRow("模型",self.model)
        self.key=QLineEdit();self.key.setEchoMode(QLineEdit.EchoMode.Password);self.key.setPlaceholderText("留空保留旧密钥；Windows 使用当前用户 DPAPI 加密");f.addRow("API Key",self.key)
        self.button(f,"保存 API 配置",self.save_ai);self.button(f,"删除密钥",lambda:(self.vault.clear(),self.notice("密钥已删除")))
        note=QLabel("未完成：服饰绑定、真实照片重建、幼年/老年独立模型、复杂家具攀爬、Live2D、移动端。默认照片动作由参考图 AI 补全；请以照片为长相依据。");note.setWordWrap(True);l.addWidget(note)
    def interaction_pref(self,key,value):
        self.set_pref(key,value)
        if (key=="sound" and not value) or (key=="volume" and value==0):self.pet.audio.stop()
        if key=="cursor_chase" and not value:self.pet.cursor_target=None;self.pet.cursor_mode=False
        if key=="input_link" and value and not self.pet.keyboard.supported:self.notice("全局打字联动需要 Windows；当前平台仅可手动预览动作")
    def preview_sound(self):
        ok=self.pet.audio.play(self.sound_choice.currentData(),True)
        self.notice("正在试听合成音效" if ok else "请先开启声音并调高音量；自动播放需要 Windows 音频设备")
    def save_birth(self):self.engine.data["birth_date"]=self.birth.date().toString("yyyy-MM-dd");self.engine.save();self.refresh();self.notice("生日已更新")
    def reset_age(self):self.engine.data["age_override"]=None;self.engine.data["age_frozen"]=False;self.engine.save();self.refresh()
    def save_ai(self):
        try:
            base=checked_base(self.base_url.text())
            if not self.model.text().strip():raise ValueError("模型名不能为空")
            if self.key.text().strip():self.vault.save(self.key.text());self.key.clear()
            self.engine.data["ai"].update(enabled=self.ai_enabled.isChecked(),diary_enabled=self.ai_diary.isChecked(),base_url=base,model=self.model.text().strip()[:120]);self.engine.save();self.notice("API 配置已保存；密钥不写入普通 JSON")
        except (ValueError,OSError) as exc:self.notice(str(exc))
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
        self.motion_current.setText("当前动作："+MOTIONS.get(self.pet.behaviour.state,MOTIONS["idle"]).label+"  ·  体验情绪："+self.pet.director.mood(self.engine.mood))
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
        self.shop_selection()
    def closeEvent(self,event):
        self.engine.save();event.ignore();self.hide()
    def shutdown(self):
        self.timer.stop()
        if self.home:self.home.close()
        self.hide()
