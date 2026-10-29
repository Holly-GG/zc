"""Local-first multifunction dashboard. The desktop pet remains a separate window."""
import json,uuid,sys
from pathlib import Path
from datetime import date
from PySide6.QtCore import Qt,QTimer,QDate,QEvent,QSize
from PySide6.QtGui import QPixmap,QPainter,QColor,QIcon
from PySide6.QtWidgets import (QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,
    QListWidget,QStackedWidget,QScrollArea,QProgressBar,QComboBox,QSpinBox,QDoubleSpinBox,QTextBrowser,
    QFrame,QLineEdit,QTextEdit,QCheckBox,QCalendarWidget,QFileDialog,QDateEdit,QGroupBox,QFormLayout,QTabWidget)
from ..art import asset_path
from .engine import STAT_NAMES
from .catalog import BY_ID,is_placeable
from .profile import sanitize_profile
from .item_art import item_pixmap
from ..desktop_items import ItemDragCard
from ..ui_controls import ClickSelectComboBox,ExplicitSpinBox
from .ai import SecretVault,AIClient,checked_base
from .jobs import run_job
from ..theme import STYLE,STATE_COLORS
from ..journal import PaperPage,ChapterHeading,JournalSidebar,HeroIllustration,portrait
from ..theme import chapter_style
from ..journal import navigation_icon
from ..journal_components import PaperCard,ResponsiveColumns,CardGrid,StateRing,StateStrip,CareButton,CategoryTabs,PoseStrip
from ..interaction.actions import ACTIONS as MOTIONS,MOOD_POOLS,SOUNDS
ACTIONS={key:info.label for key,info in MOTIONS.items()}
PENDING=["跳上真实家具","精确三维攀爬与肢体接触","服饰穿戴","幼猫/老年独立模型","更连贯的长帧动作"]
class MoodCurve(QWidget):
    def __init__(self,engine):super().__init__();self.engine=engine;self.setMinimumHeight(110)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.fillRect(self.rect(),QColor("#E8E9C0"))
        values=[e["value"] for e in self.engine.data["mood_history"][-80:]]
        if len(values)<2:p.setPen(QColor("#2A472F"));p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,"陪伴一会儿，心情曲线就会长出来")
        else:
            p.setPen(QColor("#3C582C"))
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
        label.setWordWrap(True)
        self.clock_label=QLabel();self.clock_label.setObjectName("eyebrow");brand.addWidget(self.clock_label)
        self.skin_return_button=QPushButton('参考原图');self.skin_return_button.clicked.connect(self.enter_skin);self.skin_return_button.hide()
        self.skin_return_button.setToolTip('查看参考原图与旧版热点；返回“完整功能”继续使用分层界面')
        for text,callback in [("随机待机",lambda:self.pet.set_work_mode(not self.pet.work_mode)),("专注小窗",self.pet.open_focus),("整理桌面",self.pet.desktop.clear)]:
            button=QPushButton(text);button.setObjectName("quiet");button.clicked.connect(callback);top.addWidget(button)
        outer.addWidget(header);row=QHBoxLayout();row.setSpacing(12);outer.addLayout(row,1)
        sidebar=JournalSidebar();sidebar.setObjectName("sidebar");sidebar.setFixedWidth(156);side=QVBoxLayout(sidebar);side.setContentsMargins(8,12,8,8)
        mark=QLabel();mark.setAlignment(Qt.AlignmentFlag.AlignCenter);mark.setPixmap(self.chapter_portrait(0).scaled(36,36,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation));side.addWidget(mark)
        label=QLabel("小棕点值班室");label.setAlignment(Qt.AlignmentFlag.AlignCenter);label.setObjectName("eyebrow");side.addWidget(label)
        side.setSpacing(4)
        self.nav=QListWidget();self.nav.setObjectName("navigation");self.nav.setIconSize(QSize(18,18));side.addWidget(self.nav,1);self.stack=QStackedWidget();row.addWidget(sidebar)
        content_column=QVBoxLayout();content_column.setContentsMargins(0,0,0,0);content_column.setSpacing(8);row.addLayout(content_column,1);content_column.addWidget(self.stack,1)
        self.status=QLabel("本地陪伴 · 档案随时保存 · 今天也慢慢来");self.status.setObjectName("sub");self.status.setWordWrap(True);outer.addWidget(self.status)
        builders=[("陪伴总览",self.overview),("照料与动作",self.care_page),("年糕小铺",self.shop_page),("我的背包",self.backpack_page),
                  ("专注与待办",self.focus_page),("和年糕聊天",self.chat_page),("年糕日记",self.diary_page),("性格与设置",self.settings_page),("宠物相册",self.album_page)]
        for index,(name,builder) in enumerate(builders):
            self._chapter_index=index
            from ..component_skin import stylesheet,PAGE_KEYS
            self.nav.addItem(name);self.nav.item(index).setIcon(navigation_icon(index));page=PaperPage(index);page.setStyleSheet(chapter_style(page.chapter)+stylesheet(PAGE_KEYS[index]));layout=QVBoxLayout(page);layout.setContentsMargins(22,16,22,20);layout.setSpacing(10);builder(layout);layout.addStretch()
            scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);scroll.setWidget(page);self.stack.addWidget(scroll)
        content_column.addWidget(self.chat_composer)
        self.chat_composer.hide()
        self.nav.currentRowChanged.connect(lambda index:self.chat_composer.setVisible(index==5))
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex);self.nav.setCurrentRow(0)
        from ..component_skin import stylesheet
        self.setStyleSheet(STYLE+stylesheet('home'))
        self.pet.desktop.changed.connect(self.refresh_inventory)
        self.skin_view=None;self.presentation=None
        self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(1000);self.refresh()
        from ..skin_pack import SkinPack
        try:
            self.install_skin(SkinPack.active(self.pet.settings.path.parent) or SkinPack.bundled())
            self.show_classic(0)
            self.resize(width,height)
        except (OSError,ValueError) as exc:self.notice('整页图暂不可用，保留完整界面：'+str(exc))
    def install_skin(self,pack):
        from ..skin_view import FullPageView
        if self.presentation is None:
            classic=self.takeCentralWidget();self.presentation=QStackedWidget();self.setCentralWidget(self.presentation);self.presentation.addWidget(classic)
            self.nav.currentRowChanged.connect(self.route_skin)
        elif self.skin_view:
            self.skin_view.release();self.presentation.removeWidget(self.skin_view);self.skin_view.deleteLater()
        self.skin_view=FullPageView(self,pack);self.presentation.addWidget(self.skin_view)
        area=self.screen().availableGeometry();self.resize(min(1200,area.width()-24),min(751,area.height()-56));self.enter_skin()
    def enter_skin(self):
        if not self.skin_view:return
        index=self.nav.currentRow();page={0:'home',1:'care',3:'backpack',5:'chat',6:'diary',7:'settings',8:'album'}.get(index,'home')
        self.presentation.setCurrentIndex(1);self.skin_view.show_page(page)
    def show_classic(self,index=None):
        if self.skin_view:self.skin_view.release();self.skin_view.page=None
        if self.presentation:self.presentation.setCurrentIndex(0)
        if index is not None:self.nav.setCurrentRow(index);self.stack.setCurrentIndex(index)
    def route_skin(self,index):
        if self.skin_view and self.presentation.currentIndex()==1:
            page={0:'home',1:'care',3:'backpack',5:'chat',6:'diary',7:'settings',8:'album'}.get(index)
            self.skin_view.show_page(page) if page else self.show_classic(index)
    def import_skin(self):
        path,_=QFileDialog.getOpenFileName(self,'导入八张整页参考图ZIP','','ZIP (*.zip)')
        if not path:return
        from ..skin_pack import import_skin_zip
        try:self.install_skin(import_skin_zip(path,self.pet.settings.path.parent));self.notice('整页底图已载入，使用真实控件叠加')
        except (OSError,ValueError,__import__('zipfile').BadZipFile) as exc:self.notice('底图导入失败：'+str(exc))
    def chapter_portrait(self,index):
        if index==8:return QPixmap()  # New page has no approved dedicated character art.
        image=portrait(index)
        if not image.isNull():return image
        frames=self.pet.art.frames.get('idle')
        return QPixmap.fromImage(frames[0]) if frames else QPixmap()
    def title(self,layout,title,subtitle=""):
        if layout.property('hasHeading'):
            label=QLabel(title);label.setObjectName('sectionTitle');layout.addWidget(label);return
        layout.setProperty('hasHeading',True)
        index=self._chapter_index
        layout.addWidget(ChapterHeading(index,title,subtitle,self.chapter_portrait(3 if index==1 else index)))
        destinations={0:((7,'编辑档案'),(6,'写下今天')),1:((3,'打开背包'),),2:((3,'查看已购小物'),),
                      3:((2,'前往年糕小铺'),),4:((6,'记录专注日常'),),5:((7,'API 与聊天设置'),),
                      6:((8,'打开宠物相册'),),7:((5,'返回聊天'),),8:((6,'打开日记'),)}
        links=QHBoxLayout();links.setSpacing(8)
        for target,text in destinations.get(index,()):
            link=QPushButton(text+' →');link.setObjectName('pageLink');link.setAccessibleName(text);link.setMinimumHeight(36)
            link.clicked.connect(lambda checked=False,destination=target:self.nav.setCurrentRow(destination));links.addWidget(link)
        links.addStretch();layout.addLayout(links)
    def button(self,layout,text,callback):
        b=QPushButton(text);b.clicked.connect(lambda _checked=False:callback());layout.addWidget(b);return b
    def notice(self,text):
        message=str(text);self.status.setTextFormat(Qt.TextFormat.PlainText);self.status.setText(message.splitlines()[0][:240] if message else '');self.status.setToolTip(message)
        if getattr(self,'skin_view',None) and self.presentation.currentIndex()==1:self.skin_view.show_toast(message)
    def result(self,result):self.notice(result[1]);self.refresh()
    def overview(self,l):
        self.overview_tabs=QTabWidget();l.addWidget(self.overview_tabs)
        home=QWidget();home_layout=QVBoxLayout(home);home_layout.setContentsMargins(0,8,0,0);home_layout.setSpacing(12)
        self.overview_tabs.addTab(home,'首页 · Daily Life')
        self.home_composition(home_layout)
        from ..reference_scenes import StatusChapter
        self.status_chapter=StatusChapter(self.engine);self.overview_tabs.addTab(self.status_chapter,'宠物状态 · Pet Status')
    def home_composition(self,l):
        illustration=PaperCard();illustration.body.addWidget(HeroIllustration())
        line=QLabel('A cat. A diary. A brighter day.');line.setObjectName('scriptTitle');line.setWordWrap(True);line.setAlignment(Qt.AlignmentFlag.AlignCenter);illustration.body.addWidget(line)
        profile=PaperCard()
        self.title(profile.body,'你好，今天也有年糕陪你','月光很温柔，而你也一直在。')
        self.age_label=QLabel();self.age_label.setWordWrap(True);profile.body.addWidget(self.age_label)
        self.summary=QLabel();self.summary.setWordWrap(True);profile.body.addWidget(self.summary);self.bars={};grid=CardGrid(120,3);profile.body.addWidget(grid)
        icons=('food_bowl','brush','ball','affection','health_kit')
        for i,(key,name) in enumerate(STAT_NAMES.items()):
            bar=StateStrip(name,STATE_COLORS[key],icons[i]);self.bars[key]=bar
        grid.set_cards(self.bars.values())
        profile.body.addWidget(PoseStrip())
        l.addWidget(ResponsiveColumns(illustration,profile,(4,6),570))
        actions=QHBoxLayout();l.addLayout(actions);self.button(actions,"每日打卡 +15",lambda:self.result(self.engine.checkin()));self.button(actions,"五分钟虚拟旅行",lambda:self.result(self.engine.start_trip()))
        mood=PaperCard('今日心情','把小小的快乐，慢慢存起来。');self.curve=MoodCurve(self.engine);mood.body.addWidget(self.curve)
        notes=PaperCard('陪伴记录');self.events=QTextBrowser();self.events.setMaximumHeight(180);notes.body.addWidget(self.events);l.addWidget(ResponsiveColumns(mood,notes,(1,1),600))
    def care_page(self,l):
        self.title(l,"互动与照料","和年糕一起，把日常过得柔软一点。照料有20秒冷却，数值不代表真实健康诊断。")
        main_cards=CardGrid(152,3);l.addWidget(main_cards);extra_cards=CardGrid(152,3);l.addWidget(extra_cards);primary=[];extra=[]
        for i,(key,text,action) in enumerate([("meal","基础餐","feed"),("water","喝水","idle"),("pet","摸摸头","pet"),("play","逗猫玩","play_bow"),
             ("brush","梳毛","groom"),("bath","虚拟清洁","groom"),("litter","清猫砂","idle"),("rest","休息","sleep"),("checkup","虚拟健康照料","idle")]):
            icon_id={'meal':'food_bowl','water':'water_bowl','pet':'affection','play':'wand','brush':'brush','bath':'wash_basin','litter':'litter','rest':'bed','checkup':'health_kit'}[key]
            b=CareButton(text,icon_id);(primary if key in ('meal','water','pet','play','brush','rest') else extra).append(b);b.clicked.connect(lambda checked=False,k=key,a=action:self.care(k,a))
        main_cards.set_cards(primary);extra_cards.set_cards(extra)
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
        self.title(l,"年糕小铺","挑一件生活小物，收藏温柔的日常。购买后在背包中摆放。")
        self.shop_wallet=QLabel();l.addWidget(self.shop_wallet)
        self.shop_filter=QComboBox();self.shop_filter.addItems(["全部"]+sorted(set(v["category"] for v in BY_ID.values())))
        self.shop_filter.currentTextChanged.connect(self.render_shop);l.addWidget(CategoryTabs(self.shop_filter))
        self.shop_container=CardGrid();self.shop_grid=self.shop_container.grid;l.addWidget(self.shop_container)
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
            self.shop_cards[id]=card
        self.shop_container.set_cards(self.shop_cards.values())
    def buy_item(self,id):
        self.result(self.engine.buy(id));self.render_shop();self.render_backpack()
    def backpack_page(self,l):
        self.title(l,"森林小背包","收藏生活的小物。按住图像拖到窗口外摆放，Esc可取消。")
        row=QHBoxLayout();l.addLayout(row);self.clear_desktop_button=self.button(row,"一键清理桌面摆件",self.pet.desktop.clear)
        self.desktop_count=QLabel();row.addWidget(self.desktop_count)
        self.bag_filter=QComboBox();self.bag_filter.addItems(['全部']+sorted({v['category'] for v in BY_ID.values()}));self.bag_filter.currentTextChanged.connect(self.render_backpack);l.addWidget(CategoryTabs(self.bag_filter))
        self.bag_container=CardGrid();self.bag_grid=self.bag_container.grid;l.addWidget(self.bag_container)
        self.bag_empty=QLabel('这个分类还没有收藏。可以到年糕小铺挑一件小物。');self.bag_empty.setWordWrap(True);self.bag_empty.setObjectName('emptyState');l.addWidget(self.bag_empty);self.render_backpack()
    def render_backpack(self):
        if not hasattr(self,"bag_grid"):return
        self.clear_grid(self.bag_grid);self.bag_cards={}
        ids=[id for id,n in self.engine.data["inventory"].items() if n>0 and id in BY_ID and (self.bag_filter.currentText()=='全部' or BY_ID[id]['category']==self.bag_filter.currentText())]
        for i,id in enumerate(ids):
            card=ItemDragCard(id,self.pet,self,"放到桌面" if is_placeable(id) else "使用",lambda item=id:self.place_or_use(item))
            count=self.engine.data["inventory"].get(id,0);available=self.pet.desktop.available(id)
            card.detail.setText("拥有 "+str(count)+" · 可摆 "+str(available))
            card.button.setEnabled(BY_ID[id]["ready"] and (available>0 or not is_placeable(id)))
            self.bag_cards[id]=card
        self.bag_container.set_cards(self.bag_cards.values());self.bag_empty.setVisible(not ids)
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
        group=QGroupBox("把照料用品摆到桌面");g=QVBoxLayout(group);l.addWidget(group)
        grid=CardGrid(160,3);g.addWidget(grid);cards=[]
        ids=["food_bowl","water_bowl","water_fountain","wand","ball","brush","wash_basin","litter","bed","health_kit"]
        for i,id in enumerate(ids):
            card=ItemDragCard(id,self.pet,self,"摆放",lambda item=id:self.result(self.pet.desktop.place(item)))
            card.detail.setText("拖出可摆放 · 点击实物互动");cards.append(card)
        grid.set_cards(cards)
        self.button(l,"一键清理桌面摆件",self.pet.desktop.clear)
    def focus_page(self,l):
        self.title(l,"一起专注，好好休息","计时依据真实经过时间。退出后暂停，不补发离线奖励。")
        timer=PaperCard('安静的一小时','先做一件小事，年糕陪你慢慢完成。')
        self.focus_label=QLabel();self.focus_label.setObjectName('focusClock');timer.body.addWidget(self.focus_label)
        self.minutes=QSpinBox();self.minutes.setRange(1,180);self.minutes.setValue(25);self.minutes.setSuffix(' 分钟');timer.body.addWidget(self.minutes)
        controls=QHBoxLayout();timer.body.addLayout(controls)
        self.button(controls,'开始',lambda:self.engine.focus_start(self.minutes.value()));self.button(controls,'暂停',self.engine.focus_pause);self.button(controls,'继续',self.engine.focus_resume)
        self.button(timer.body,'打开专注小窗',self.pet.open_focus)
        self.button(timer.body,'切换随机待机工作模式',lambda:self.pet.set_work_mode(not self.pet.work_mode))
        self.dday=QDateEdit();self.dday.setCalendarPopup(True);self.dday.setDate(QDate.currentDate());timer.body.addWidget(QLabel('纪念日 / 倒计时'));timer.body.addWidget(self.dday)
        self.button(timer.body,'保存倒计时',lambda:self.set_pref('d_day',self.dday.date().toString('yyyy-MM-dd')));self.dday_label=QLabel();self.dday_label.setWordWrap(True);timer.body.addWidget(self.dday_label)
        tasks=PaperCard('今日待办','每完成一件小事，都值得轻轻庆祝。')
        self.tasks=QListWidget();self.tasks.setWordWrap(True);self.tasks.setMinimumHeight(220);self.tasks.itemChanged.connect(self.task_changed);tasks.body.addWidget(self.tasks)
        self.task_input=QLineEdit();self.task_input.setPlaceholderText('写下一件今天想完成的小事');self.task_input.returnPressed.connect(self.add_task);tasks.body.addWidget(self.task_input);self.button(tasks.body,'添加待办',self.add_task)
        l.addWidget(ResponsiveColumns(timer,tasks,(1,1),600));self.render_tasks()
    def render_tasks(self):
        self.tasks.blockSignals(True);self.tasks.clear()
        for task in self.engine.data["tasks"][-200:]:
            from PySide6.QtWidgets import QListWidgetItem
            item=QListWidgetItem(task["text"]);item.setToolTip(task['text']);item.setData(Qt.ItemDataRole.UserRole,task["id"]);item.setFlags(item.flags()|Qt.ItemFlag.ItemIsUserCheckable);item.setCheckState(Qt.CheckState.Checked if task["done"] else Qt.CheckState.Unchecked)
            if task["done"]:item.setFlags(item.flags()&~Qt.ItemFlag.ItemIsEnabled)
            self.tasks.addItem(item)
        self.tasks.blockSignals(False)
    def task_changed(self,item):
        if item.checkState()==Qt.CheckState.Checked:self.engine.complete_task(item.data(Qt.ItemDataRole.UserRole));self.render_tasks();self.refresh()
    def add_task(self):
        if self.engine.add_task(self.task_input.text()):self.task_input.clear();self.render_tasks()
    def chat_page(self,l):
        self.chat_busy=False;self.chat_channel=self.pet.chat_channels['main']
        self.title(l,"和年糕聊天","本地回应默认开启；只有启用API后才联网，不读取应用内容。")
        l.setSpacing(8)
        from ..chat_widgets import TokenMeter,SessionChooser,HistoryBrowser
        self.chat_chooser=SessionChooser(self.pet,self.chat_channel,self.load_chat,lambda:self.chat_busy);l.addWidget(self.chat_chooser)
        self.chat_log=QTextBrowser();self.chat_log.setObjectName('chatTranscript');self.chat_log.setMinimumHeight(240);l.addWidget(self.chat_log);self.chat_input=QLineEdit();self.chat_input.setMaxLength(65536);self.chat_input.setPlaceholderText("今天发生了什么？");self.chat_input.returnPressed.connect(self.send_chat)
        self.chat_composer=QFrame();self.chat_composer.setObjectName('chatComposer')
        entry=QHBoxLayout(self.chat_composer);entry.setContentsMargins(12,8,12,8);entry.setSpacing(8);entry.addWidget(self.chat_input,1)
        self.chat_send=self.button(entry,"发送",self.send_chat);self.chat_send.setObjectName("primary")
        self.chat_meter=TokenMeter(self.pet,self.chat_channel,self.chat_input);l.addWidget(self.chat_meter)
        from PySide6.QtWidgets import QToolButton
        toggle=QToolButton();toggle.setText('按日期查看完整本地历史 ▸');toggle.setCheckable(True);l.addWidget(toggle)
        group=QGroupBox('完整历史');box=QVBoxLayout(group);self.chat_archive=HistoryBrowser(self.pet);box.addWidget(self.chat_archive);l.addWidget(group);group.hide();toggle.toggled.connect(group.setVisible);self.load_chat()
    def load_chat(self,id=None):
        from ..chat_widgets import transcript_html
        if hasattr(self,'chat_log'):self.chat_log.setHtml(transcript_html(self.pet.chat_store,id or self.chat_channel.session_id))

    def send_chat(self):
        if self.chat_busy:return
        text=self.chat_input.text()
        if not text.strip():return
        self.chat_input.clear();self.chat_log.append("你："+__import__("html").escape(text))
        if text in ("年糕最可爱","小棕点"):self.engine.unlock_badge("鼻尖小棕点")
        if not self.engine.data["ai"]["enabled"]:
            from ..dialogue import respond
            reply=respond(text);self.chat_channel.local(self.engine.data["ai"],text,reply);self.load_chat();self.chat_archive.reset();self.chat_meter.refresh();return
        self.chat_busy=True;self.chat_input.setEnabled(False);self.chat_send.setEnabled(False);mood=self.engine.mood;history=list(self.history)
        def restore():self.chat_busy=False;self.chat_input.setEnabled(True);self.chat_send.setEnabled(True)
        def done(reply):
            if self.pet.shutting_down:return
            restore();self.chat_chooser.refresh();self.load_chat();self.chat_meter.refresh();self.chat_archive.reset();self.calibrate_date()
            self.notice("已摘要并自动新建承接会话，原始历史完整保留" if self.chat_channel.last_rollover else "回复已保存到本地")
        def failed(message):
            if self.pet.shutting_down:return
            restore();self.notice(message);self.chat_log.append("请求未完成："+__import__('html').escape(message));self.chat_input.setText(text);self.chat_archive.reset();self.chat_meter.refresh()
        run_job(lambda:self.chat_channel.send(self.client,text,mood),done,failed)
    def calibrate_date(self):
        if self.engine.data["preferences"]["network_time"] and self.client.server_time:self.engine.calibrate_time(self.client.server_time);self.refresh()
    def diary_page(self,l):
        self.title(l,"魔法手账","记录与年糕一起的平凡日常。AI日记需单独开启，记录保存在本机。")
        from .calendar_widget import ChineseCalendar
        index=PaperCard('日历与记录');self.calendar=ChineseCalendar();self.calendar.setMaximumHeight(300);self.calendar.selectionChanged.connect(self.load_diary);index.body.addWidget(self.calendar)
        self.diary_index=QListWidget();self.diary_index.setMinimumHeight(100);self.diary_index.itemClicked.connect(self.select_diary);index.body.addWidget(self.diary_index)
        self.button(index.body,'打开本地相册',lambda:self.nav.setCurrentRow(8))
        paper=PaperCard('给今天留一句话');self.calendar_info=QLabel();self.calendar_info.setWordWrap(True);self.calendar_info.setObjectName('sub');paper.body.addWidget(self.calendar_info)
        self.diary_source=QLabel();self.diary_source.setWordWrap(True);self.diary_source.setObjectName('eyebrow');paper.body.addWidget(self.diary_source)
        self.diary_text=QTextEdit();self.diary_text.setMinimumHeight(230);self.diary_text.setPlaceholderText('记录此刻的想法……');paper.body.addWidget(self.diary_text)
        self.diary_note=QTextEdit();self.diary_note.setPlaceholderText('补充一条自己的备注');self.diary_note.setMaximumHeight(85);paper.body.addWidget(self.diary_note)
        row=QHBoxLayout();paper.body.addLayout(row);self.button(row,'生成本地日记',self.generate_diary);self.button(row,'生成AI日记',self.generate_ai_diary)
        self.button(paper.body,'保存日记',self.save_diary).setObjectName('primary')
        row=QHBoxLayout();paper.body.addLayout(row);self.button(row,'导出TXT',lambda:self.export_diary('txt'));self.button(row,'导出PNG',lambda:self.export_diary('png'))
        from ..reference_scenes import SpecimenStrip
        paper.body.addWidget(QLabel('草药标本图鉴 · Botanical Notes'))
        paper.body.addWidget(SpecimenStrip())
        l.addWidget(ResponsiveColumns(index,paper,(2,3),720));self.load_diary()
    def select_diary(self,item):
        if not item.data(Qt.ItemDataRole.UserRole):return
        self.calendar.setSelectedDate(QDate.fromString(item.data(Qt.ItemDataRole.UserRole),'yyyy-MM-dd'))
    def refresh_diary_index(self):
        from PySide6.QtWidgets import QListWidgetItem
        selected=self.diary_day();self.diary_index.clear()
        for day,record in sorted(self.engine.data['diaries'].items(),reverse=True):
            item=QListWidgetItem(day+' · '+(record.get('text','').split('\n')[0][:18] or '手写记录'));item.setData(Qt.ItemDataRole.UserRole,day);self.diary_index.addItem(item)
            if day==selected:self.diary_index.setCurrentItem(item)
        if self.diary_index.count()==0:self.diary_index.addItem('还没有日记，写下第一条记录吧。')
    def diary_day(self):return self.calendar.selectedDate().toString("yyyy-MM-dd")
    def load_diary(self):
        from .calendar_cn import china_now,lunar_label
        self.calendar_info.setText(self.diary_day()+" · "+lunar_label(date.fromisoformat(self.diary_day()),True)+"\n中国标准时间 UTC+08:00 · 2020–2069")
        self.refresh_diary_index()
        record=self.engine.data["diaries"].get(self.diary_day(),{});self.diary_text.setPlainText(record.get("text",""));self.diary_note.setPlainText(record.get("note",""));self.diary_source.setText(record.get("source","这一天还没有日记"))
    def generate_diary(self):self.engine.local_diary(self.diary_day());self.load_diary();self.notice("已根据实际游戏事件生成")
    def save_diary(self):
        day=self.diary_day();old=self.engine.data["diaries"].get(day,{})
        self.engine.data["diaries"][day]=dict(text=self.diary_text.toPlainText()[:20000],note=self.diary_note.toPlainText()[:10000],source=old.get("source","手动记录"));self.engine.save();self.refresh_diary_index();self.notice("日记已保存")
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
        self.title(l,"性格与设置","为年糕打造更舒适的生活方式。档案与设置保存在本机。")
        from PySide6.QtWidgets import QToolButton
        compatibility=QToolButton();compatibility.setText('素材与旧版整图兼容工具 ▸');compatibility.setCheckable(True);l.addWidget(compatibility)
        reference_box=QWidget();references=QHBoxLayout(reference_box);references.setContentsMargins(0,0,0,0);references.setSpacing(8);l.addWidget(reference_box);reference_box.hide();compatibility.toggled.connect(reference_box.setVisible)
        self.button(references,'参考原图预览',self.enter_skin).setObjectName('quiet')
        self.button(references,'导入原图 ZIP',self.import_skin).setObjectName('quiet');references.addStretch()
        group=QGroupBox("年糕档案 · 每次API请求读取");form=QFormLayout(group);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows);form.setSpacing(12);self.profile_fields={}
        from ..reference_scenes import ScenePortrait
        aside=PaperCard('只为年糕');aside.body.addWidget(ScenePortrait('settings',self.chapter_portrait(7),350))
        badge=QLabel('年糕插画待确认');badge.setObjectName('candidate');aside.body.addWidget(badge)
        identity=QLabel('Niangao / 年糕\n布偶猫 · 男孩子\n每一次回复，都记得你的习惯。');identity.setWordWrap(True);aside.body.addWidget(identity);l.addWidget(ResponsiveColumns(aside,group,(1,3),780,True))
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
        self.api_tokens=ExplicitSpinBox();self.api_tokens.setRange(64,2048);self.api_tokens.setValue(self.engine.data["ai"]["max_tokens"]);f.addRow("轻量输出上限",self.api_tokens)
        self.api_timeout=ExplicitSpinBox();self.api_timeout.setRange(10,180);self.api_timeout.setSuffix(" 秒");self.api_timeout.setValue(self.engine.data["ai"]["timeout"]);f.addRow("请求超时",self.api_timeout)
        hint=QLabel("模型 ID 以服务商控制台为准；预设不代表所有账户可用。支持基础地址或完整接口地址。仅允许轻量思考，不再自动抬高输出预算；测试和摘要也计入每日额度。");hint.setWordWrap(True);f.addRow(hint)
        self.context_window=ExplicitSpinBox();self.context_window.setRange(4096,2000000);f.addRow("此模型上下文窗口",self.context_window)
        self.context_threshold=ExplicitSpinBox();self.context_threshold.setRange(1024,2000000);f.addRow("摘要阈值（保守 token）",self.context_threshold)
        self.daily_tokens=ExplicitSpinBox();self.daily_tokens.setRange(1000,100000000);self.daily_tokens.setValue(self.engine.data['ai']['daily_token_limit']);f.addRow("本程序每日 token 上限",self.daily_tokens)
        self.daily_warning=ExplicitSpinBox();self.daily_warning.setRange(10,99);self.daily_warning.setSuffix(" % 已用时提醒");self.daily_warning.setValue(self.engine.data['ai']['daily_warning_percent']);f.addRow("用量提醒阈值",self.daily_warning)
        self.load_context_profile();self.model.editingFinished.connect(self.load_context_profile);self.base_url.editingFinished.connect(self.load_context_profile);self.api_protocol.activated.connect(self.load_context_profile)
        note=QLabel("阈值按地址+协议+模型分别保存，请以服务商真实窗口为准。发送前保守估算，不是官方精确 tokenizer；服务商返回 usage 后按实际用量记账。思考专用模型会拦截。历史 SQLite 和逐会话 JSON 永不自动清理。");note.setWordWrap(True);f.addRow(note)
        self.key=QLineEdit();self.key.setEchoMode(QLineEdit.EchoMode.Password);self.key.setPlaceholderText("留空保留旧密钥；Windows 使用当前用户 DPAPI 加密");f.addRow("API Key",self.key)
        self.button(f,"保存 API 配置",self.save_ai);self.button(f,"删除密钥",lambda:(self.vault.clear(),self.notice("密钥已删除")))
        self.api_test_button=self.button(f,"保存并测试连接",self.test_api_connection)
        self.api_result=QLabel("密钥仅在本机填写，不要发送到聊天窗口。");self.api_result.setWordWrap(True);f.addRow(self.api_result)
        note=QLabel("未完成：服饰绑定、真实照片重建、幼年/老年独立模型、复杂家具攀爬、Live2D、移动端。默认照片动作由参考图 AI 补全；请以照片为长相依据。");note.setWordWrap(True);l.addWidget(note)
    def album_page(self,l):
        self.title(l,'收藏每一个小日子','照片留在本机，按日期整理。原文件不会移动，也不会发送到API。')
        from ..album_page import AlbumPage
        self.album_widget=AlbumPage(self.pet,self.notice);l.addWidget(self.album_widget)
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
    def load_context_profile(self,*_):
        from .token_budget import policy
        if not hasattr(self,'context_window'):return
        try:p=policy(dict(self.engine.data['ai'],base_url=self.base_url.text(),model=self.model.text(),protocol=self.api_protocol.currentData()))
        except ValueError:p={'window':32768,'threshold':28000}
        self.context_window.setValue(p['window']);self.context_threshold.setValue(p['threshold'])
    def apply_api_preset(self,index):
        from .providers import PRESETS
        _,protocol,base,model=PRESETS[index]
        self.api_protocol.setCurrentIndex(self.api_protocol.findData(protocol))
        if base:self.base_url.setText(base)
        self.model.setText(model);self.model.setPlaceholderText("填写此账户控制台可用的模型 / endpoint ID")
        self.load_context_profile();self.key.clear()
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
            if self.context_threshold.value()>=self.context_window.value():raise ValueError("摘要阈值必须小于模型上下文窗口")
            from .token_budget import identity
            profile_key=identity(dict(self.engine.data['ai'],base_url=base,model=self.model.text().strip(),protocol=self.api_protocol.currentData()))
            self.engine.data['ai']['context_profiles'][profile_key]={'window':self.context_window.value(),'threshold':self.context_threshold.value(),'keep':6}
            self.engine.data['ai'].update(light_thinking=True,daily_token_limit=self.daily_tokens.value(),daily_warning_percent=self.daily_warning.value())
            if self.key.text().strip():self.vault.save(self.key.text());self.key.clear()
            self.api_platform_changed=False
            self.engine.data["ai"].update(enabled=self.ai_enabled.isChecked(),diary_enabled=self.ai_diary.isChecked(),base_url=base,model=self.model.text().strip()[:200],protocol=self.api_protocol.currentData(),max_tokens=self.api_tokens.value(),timeout=self.api_timeout.value());self.engine.save()
            if self.pet.work_panel:self.pet.work_panel.sync_config()
            self.chat_chooser.refresh();self.load_chat()
            self.notice("API 配置已保存；密钥不写入普通 JSON");return True
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
        if self.skin_view and self.presentation.currentIndex()==1:self.skin_view.refresh()
        rows=self.pet.desktop.status_rows();self.desktop_status.setText("\n".join(rows) if rows else "桌面还空着，把一只粮碗或猫砂盆从背包拖出来吧。")
        self.motion_current.setText("当前动作："+MOTIONS.get(self.pet.work_pose if self.pet.work_mode else self.pet.behaviour.state,MOTIONS["idle"]).label+"  ·  体验情绪："+self.pet.director.mood(self.engine.mood))
        e=self.engine;a=e.age();self.age_label.setText("年糕 NIANGAO · 布偶猫 · 男孩子\n"+a["text"]+" · "+a["stage"]+" · 约人类 "+str(a["human_years"])+" 岁"+("\n体验年龄已冻结，真实生日仍保留" if e.data["age_frozen"] else ""))
        self.summary.setText(f'Lv.{e.level}  ·  经验 {e.data["xp"]}  ·  金币 {e.data["coins"]}  ·  心情 {e.mood}')
        for key,bar in self.bars.items():bar.setValue(round(e.data["stats"][key]))
        self.status_chapter.refresh()
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
        if self.skin_view:self.skin_view.release();self.skin_view.page=None
        if hasattr(self,'album_widget'):self.album_widget.cancel_import()
        self.hide()
