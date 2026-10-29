"""Original full-page artwork with aligned, real Qt input and action layers."""
from functools import lru_cache
from PySide6.QtCore import Qt,QRectF,QPointF,QSizeF,QTimer
from PySide6.QtGui import QPixmap,QPainter,QColor,QPen,QPalette
from PySide6.QtWidgets import (QGraphicsView,QGraphicsScene,QGraphicsProxyWidget,QPushButton,QLabel,QWidget,
 QFrame,QLineEdit,QTextEdit,QSlider,QMenu,QSizePolicy)
from .skin_pack import SkinPack
from .life.catalog import BY_ID
from .typography import roles

W,H=1600,1000
NAV=('home','chat','diary','album','backpack','care','status','settings')
LEGACY={'home':0,'care':1,'backpack':3,'chat':5,'diary':6,'settings':7,'album':8,'status':0}
TEXT_STYLE='''QWidget{color:#2A472F;font-family:"Niangao UI Sans";font-size:20px;}
QLabel,QTextEdit,QLineEdit,QAbstractScrollArea{border:0;background:transparent;padding:2px;}
QScrollBar:vertical{width:7px;background:transparent;}QScrollBar::handle:vertical{background:#92AB76;min-height:20px;}
QTextEdit:focus,QLineEdit:focus{border:1px solid #3E7197;border-radius:5px;}'''.replace('Niangao UI Sans',roles()['body']['family'])

def rect(box):return QRectF(box[0]*W,box[1]*H,box[2]*W,box[3]*H)

@lru_cache(maxsize=8)
def artwork(path):return QPixmap(path)

class SkinMeter(QWidget):
    def __init__(self,color,ring=False):
        super().__init__();self.color=color;self.ring=ring;self.value=0;self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents);self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        palette=self.palette();palette.setColor(QPalette.ColorRole.Window,QColor(0,0,0,0));self.setPalette(palette)
    def setText(self,value):self.value=max(0,min(100,float(value)));self.setAccessibleName(str(round(self.value))+'%');self.update()
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);w,h=self.width(),self.height()
        if self.ring:
            circle=QRectF(9,9,w-18,h-18)
            p.setPen(QPen(QColor('#FAF6E8'),17));p.drawEllipse(circle)
            p.setPen(QPen(QColor('#E1E4D0'),10));p.drawEllipse(circle)
            p.setPen(QPen(QColor(self.color),10,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap));p.drawArc(circle,90*16,-round(self.value*3.6*16))
            number=QRectF(w*.20,h*.60,w*.60,h*.26);p.fillRect(number,QColor('#FAF6E8'));p.setPen(QColor('#2A472F'));font=p.font();font.setPixelSize(29);p.setFont(font);p.drawText(number,Qt.AlignmentFlag.AlignCenter,str(round(self.value))+'%')
        else:
            p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor('#E1E4D0'));p.drawRoundedRect(QRectF(self.rect()),h/2,h/2)
            p.setBrush(QColor(self.color));p.drawRoundedRect(QRectF(0,0,w*self.value/100,h),h/2,h/2)
        p.end()

class Hotspot(QPushButton):
    def __init__(self,label,callback,visible=False):
        super().__init__(label if visible else '');self.label=label;self.visible_label=visible;self.switch=False;self.disabled_label=None
        self.setAccessibleName(label);self.setToolTip(label);self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus);self.clicked.connect(lambda checked=False:QTimer.singleShot(0,callback))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground);self.setAutoFillBackground(False)
        palette=self.palette();palette.setColor(QPalette.ColorRole.Window,QColor(0,0,0,0));palette.setColor(QPalette.ColorRole.Button,QColor(0,0,0,0));self.setPalette(palette)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.switch:
            p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor('#516D3F' if self.isChecked() else '#B9BFAB'));p.drawRoundedRect(QRectF(2,3,self.width()-4,self.height()-6),self.height()/2,self.height()/2)
            d=self.height()-12;p.setBrush(QColor('#FCFAF0'));p.drawEllipse(QRectF(self.width()-d-6 if self.isChecked() else 6,6,d,d))
        elif self.visible_label or not self.isEnabled():
            p.setBrush(QColor('#DFE7CB') if self.isChecked() else QColor(250,247,233,245));p.setPen(QPen(QColor('#8A9C70'),1));p.drawRoundedRect(QRectF(self.rect()).adjusted(1,1,-1,-1),5,5)
            p.setPen(QColor('#2A472F' if self.isEnabled() else '#66745C'));text=self.disabled_label if not self.isEnabled() and self.disabled_label else self.label;p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,p.fontMetrics().elidedText(text,Qt.TextElideMode.ElideRight,max(1,self.width()-8)))
        if self.underMouse() and self.isEnabled():p.fillRect(self.rect(),QColor(146,171,118,35))
        if self.hasFocus():p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor('#3E7197'),2));p.drawRoundedRect(QRectF(self.rect()).adjusted(2,2,-2,-2),4,4)
        p.end()

def find_layout(layout,widget):
    if layout is None:return None
    if layout.indexOf(widget)>=0:return layout
    for i in range(layout.count()):
        child=layout.itemAt(i).layout()
        found=find_layout(child,widget) if child else None
        if found:return found

class Portal:
    """Temporarily embed the original input, restoring its layout and styling on exit."""
    def __init__(self,scene,widget,box,style=TEXT_STYLE):
        self.widget=widget;self.parent=widget.parentWidget();self.layout=find_layout(self.parent.layout(),widget)
        if self.layout is None:raise ValueError('找不到控件原布局：'+widget.objectName())
        self.hidden=widget.isHidden();self.minimum=widget.minimumSize();self.maximum=widget.maximumSize();self.style=widget.styleSheet()
        self.button_text=widget.text() if isinstance(widget,QPushButton) else None
        if self.button_text is not None:widget.setAccessibleName(self.button_text);widget.setText('')
        self.placeholder=QWidget(self.parent);self.layout.replaceWidget(widget,self.placeholder)
        widget.setParent(None);widget.setMinimumSize(0,0);widget.setMaximumSize(16777215,16777215);widget.setStyleSheet(self.style+style)
        self.proxy=scene.addWidget(widget);self.proxy.setMinimumSize(QSizeF(0,0));self.proxy.setGeometry(rect(box));self.proxy.setZValue(3);widget.show()
    def restore(self):
        widget=self.widget;self.proxy.setWidget(None);widget.setParent(self.parent)
        self.layout.replaceWidget(self.placeholder,widget);self.placeholder.deleteLater()
        widget.setMinimumSize(self.minimum);widget.setMaximumSize(self.maximum);widget.setStyleSheet(self.style);widget.setVisible(not self.hidden)
        if self.button_text is not None:widget.setText(self.button_text)

class FullPageView(QGraphicsView):
    def __init__(self,host,pack):
        super().__init__();self.host=host;self.pack=pack;self.portals=[];self.page=None;self.live=[];self.checks=[];self.hotspots={};self.drag_rects={};self.album_ids=[]
        self.setScene(QGraphicsScene(0,0,W,H,self));self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setRenderHints(QPainter.RenderHint.Antialiasing|QPainter.RenderHint.SmoothPixmapTransform)
        self.setBackgroundBrush(QColor('#F5F2E4'));self.setAccessibleName('年糕整页画面与真实交互层')
        self.toast=QLabel(self.viewport());self.toast.setStyleSheet('QLabel{background:#FCFAF0;color:#2A472F;border:1px solid #92AB76;border-radius:5px;padding:7px;font-size:13px;}');self.toast.hide()
        self.toast_timer=QTimer(self);self.toast_timer.setSingleShot(True);self.toast_timer.timeout.connect(self.toast.hide)
    def resizeEvent(self,event):
        super().resizeEvent(event);self.fitInView(self.sceneRect(),Qt.AspectRatioMode.KeepAspectRatio)
        if hasattr(self,'toast'):self.toast.setGeometry(18,max(0,self.viewport().height()-53),max(1,self.viewport().width()-36),35)
    def mousePressEvent(self,event):
        self.drag_item=None
        if event.button()==Qt.MouseButton.LeftButton and self.page=='backpack':
            pos=self.mapToScene(event.position().toPoint())
            for item,box in self.drag_rects.items():
                if rect(box).contains(pos):
                    self.drag_item=item;self.drag_start=event.globalPosition().toPoint();event.accept();return
        super().mousePressEvent(event)
    def mouseMoveEvent(self,event):
        if getattr(self,'drag_item',None):event.accept();return
        super().mouseMoveEvent(event)
    def mouseReleaseEvent(self,event):
        item=getattr(self,'drag_item',None)
        if item and event.button()==Qt.MouseButton.LeftButton:
            self.drag_item=None;point=event.globalPosition().toPoint()
            if (point-self.drag_start).manhattanLength()>6 and not self.host.frameGeometry().contains(point):self.host.result(self.host.pet.desktop.place(item,point))
            event.accept();return
        super().mouseReleaseEvent(event)
    def show_toast(self,message):
        self.toast.setText(str(message).splitlines()[0][:240]);self.toast.setToolTip(str(message));self.toast.show();self.toast.raise_();self.toast_timer.start(5000)
    def release(self):
        for portal in reversed(self.portals):portal.restore()
        # A page may be switched by one of its own clicked signals. Unembed and
        # defer deletion so Qt never destroys the emitting widget in that stack.
        for item in self.scene().items():
            if isinstance(item,QGraphicsProxyWidget):
                if item.widget() is not None:
                    widget=item.widget();widget.hide();item.setWidget(None);widget.setParent(self.viewport());widget.deleteLater()
                self.scene().removeItem(item);item.deleteLater()
        self.portals=[];self.scene().clear();self.live=[];self.checks=[];self.hotspots={};self.drag_rects={};self.album_ids=[];self.album_images=[]
    def embed(self,widget,box):
        proxy=self.scene().addWidget(widget);proxy.setGeometry(rect(box));proxy.setZValue(3)
        if widget.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents):proxy.setAcceptedMouseButtons(Qt.MouseButton.NoButton);proxy.setAcceptHoverEvents(False)
        return widget
    def meter(self,key,box,ring=False):
        from .theme import STATE_COLORS
        widget=SkinMeter(STATE_COLORS[key],ring);self.embed(widget,box);self.live.append((widget,lambda:self.host.engine.data['stats'][key]));return widget
    def button(self,key,label,box,callback,visible=False):
        widget=Hotspot(label,callback,visible);widget.setStyleSheet(TEXT_STYLE+'QPushButton{background:transparent;border:0;padding:0;}');self.embed(widget,box);self.hotspots[key]=(widget,box);return widget
    def field(self,widget,box):
        portal=Portal(self.scene(),widget,box);self.portals.append(portal);return widget
    def mask(self,box,color='#FAF6E8'):
        item=self.scene().addRect(rect(box),QPen(Qt.PenStyle.NoPen),QColor(color));item.setZValue(1);return item
    def label(self,box,getter,background='#FAF6E8',size=20):
        label=QLabel();label.setWordWrap(True);label.setTextFormat(Qt.TextFormat.PlainText)
        label.setStyleSheet(TEXT_STYLE+f'QLabel{{background:{background};font-size:{size}px;padding:0;}}');label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.embed(label,box);self.live.append((label,getter));return label
    def point(self,key):
        return self.rect_point(self.hotspots[key][1])
    def rect_point(self,box):return self.viewport().mapToGlobal(self.mapFromScene(rect(box).center()))
    def widget_point(self,widget):
        portal=next(p for p in self.portals if p.widget is widget)
        return self.viewport().mapToGlobal(self.mapFromScene(portal.proxy.sceneBoundingRect().center()))
    def show_page(self,page):
        if page not in self.pack.pages:raise ValueError('未知整页图：'+page)
        self.release();self.page=page
        item=self.scene().addPixmap(artwork(str(self.pack.pages[page])))
        scale=min(W/item.pixmap().width(),H/item.pixmap().height());item.setScale(scale)
        item.setPos((W-item.pixmap().width()*scale)/2,(H-item.pixmap().height()*scale)/2)
        h=self.host
        h.nav.blockSignals(True);h.nav.setCurrentRow(LEGACY[page]);h.nav.blockSignals(False);h.stack.setCurrentIndex(LEGACY[page])
        self.navigation(page)
        if page not in ('home','chat','care'):
            clock_box=(.10,.046,.18,.022) if page=='settings' else (.033,.060,.257,.029) if page=='status' else (.024,.050,.23,.022)
            self.label(clock_box,lambda:h.clock_label.text(),size=15)
        top_boxes={'chat':[(.650,.024,.106,.057),(.763,.024,.105,.057),(.873,.024,.108,.057)],
          'settings':[(.733,.018,.071,.042),(.812,.018,.070,.042),(.888,.018,.071,.042)],
          'status':[(.692,.017,.095,.055),(.795,.017,.094,.055),(.894,.017,.098,.055)],
          'backpack':[(.730,.017,.073,.052),(.811,.017,.073,.052),(.890,.017,.095,.052)]}.get(page,[(.747,.010,.077,.052),(.831,.010,.077,.052),(.913,.010,.077,.052)])
        for i,(label,callback) in enumerate((('随机待机',lambda:h.pet.set_work_mode(not h.pet.work_mode)),('专注小窗',h.pet.open_focus),('整理桌面',h.pet.desktop.clear))):
            self.button('top'+str(i),label,top_boxes[i],callback)
        self.button('full','完整功能',(.011,.947,.105,.038),lambda:h.show_classic(LEGACY[page]),True)
        if page=='home':self.home()
        elif page=='care':self.care()
        elif page=='chat':self.chat()
        elif page=='diary':self.diary()
        elif page=='backpack':self.backpack()
        elif page=='album':self.album()
        elif page=='settings':self.settings()
        elif page=='status':self.status()
        self.refresh();self.fitInView(self.sceneRect(),Qt.AspectRatioMode.KeepAspectRatio)
    def navigation(self,page):
        # The supplied drawings have three original sidebar widths/row spacings.
        centers={'chat':(.155,.23,.306,.382,.459,.535,.613,.691),'settings':(.22,.288,.355,.423,.49,.558,.626,.694),
          'home':(.238,.305,.374,.442,.512,.582,.653,.729),'care':(.264,.330,.397,.465,.534,.602,.681,.750),
          'status':(.282,.347,.414,.480,.548,.627,.696,.774),'backpack':(.255,.322,.388,.456,.527,.595,.665,.735),
          'diary':(.292,.355,.418,.485,.549,.617,.680,.748),'album':(.254,.320,.385,.451,.519,.584,.654,.720)}[page]
        x,w,height=(.018,.148,.064) if page=='chat' else (.010,.107,.054)
        for i,target in enumerate(NAV):
            self.button('nav-'+target,target,(x,centers[i]-height/2,w,height),lambda target=target:self.show_page(target))
    def home(self):
        h=self.host;e=h.engine
        self.label((.121,.037,.21,.016),lambda:h.clock_label.text(),size=13)
        self.label((.865,.298,.065,.028),lambda:str(e.data['coins']),size=24)
        self.button('shop','年糕小铺',(.94,.293,.026,.045),lambda:h.show_classic(2))
        self.button('profile','编辑档案',(.727,.39,.055,.033),lambda:self.show_page('settings'))
        self.label((.59,.398,.13,.022),lambda:e.age()['text']+' · '+e.age()['stage'],size=15)
        self.label((.59,.427,.17,.023),lambda:e.data['birth_date'],size=17)
        self.label((.59,.458,.19,.025),lambda:e.data['profile'].get('personality') or '性格尚未填写',size=16)
        self.label((.59,.49,.19,.025),lambda:e.data['profile'].get('likes') or '喜好尚未填写',size=16)
        for i,key in enumerate(('satiety','cleanliness','energy','mood','health')):
            self.label((.514+i*.087,.582,.055,.022),lambda key=key:str(round(e.data['stats'][key]))+'%',size=16)
            self.meter(key,(.512+i*.087,.604,.061,.017))
        self.button('checkin','每日打卡',(.414,.67,.207,.132),lambda:h.result(e.checkin()))
        self.label((.462,.699,.127,.024),lambda:'今天已打卡' if e.data['daily'].get('checkin')==e.today().isoformat() else '今天还未打卡',size=15)
        self.mask((.44,.742,.17,.054));self.label((.444,.748,.165,.035),lambda:e.today().isoformat(),size=18)
        self.button('trip','五分钟虚拟旅行',(.671,.749,.126,.040),lambda:h.result(e.start_trip()))
        self.mask((.252,.858,.21,.098));self.label((.252,.858,.21,.098),lambda:e.data['diaries'].get(e.today().isoformat(),{}).get('text') or '今天还没有日记，点击记录。',size=15)
        self.button('diary','打开日记',(.14,.815,.35,.165),lambda:self.show_page('diary'))
        self.mask((.522,.824,.425,.030));self.label((.522,.824,.425,.030),lambda:'年糕插画姿态 · 当前心情：'+e.mood,size=17)
    def care(self):
        h=self.host;e=h.engine
        for i,(key,action) in enumerate((('meal','feed'),('water','idle'),('pet','pet'),('play','play_bow'),('brush','groom'),('rest','sleep'))):
            self.button('care-'+key,key,(.145+i*.141,.835,.116,.043),lambda key=key,action=action:h.care(key,action))
        self.label((.302,.934,.295,.029),lambda:e.data['events'][-1]['text'] if e.data['events'] else '还没有陪伴记录',size=16)
        self.label((.744,.933,.245,.030),lambda:'当前心情：'+e.mood,size=17)
        self.button('actions','更多照料与动作',(.76,.397,.191,.060),lambda:h.show_classic(1),True)
    def chat(self):
        h=self.host
        self.label((.307,.196,.123,.030),lambda:'API已启用' if h.engine.data['ai']['enabled'] else '本地陪伴',size=17)
        self.mask((.193,.329,.787,.526),'#EDF4F6')
        self.mask((.262,.895,.535,.044),'#FBFAF1')
        self.field(h.chat_log,(.207,.34,.755,.50));self.field(h.chat_input,(.26,.890,.548,.055))
        self.field(h.chat_send,(.866,.890,.103,.058))
        self.button('new-chat','新建会话',(.880,.275,.094,.045),h.chat_chooser.new)
        self.button('sessions','会话/历史/Token',(.434,.189,.10,.048),lambda:h.show_classic(5))
        self.button('chat-more','聊天设置与历史',(.95,.910,.026,.035),lambda:h.show_classic(5))
        self.button('attach','照片请到相册导入',(.22,.891,.028,.05),lambda:self.show_page('album'))
    def diary(self):
        h=self.host
        self.mask((.15,.265,.219,.232));self.field(h.calendar,(.15,.267,.219,.232))
        self.mask((.149,.574,.219,.375));self.field(h.diary_index,(.15,.575,.216,.37))
        self.button('new-entry','新建日记',(.31,.526,.058,.037),lambda:h.diary_text.clear())
        self.label((.409,.280,.125,.080),lambda:h.diary_day(),size=22)
        self.label((.560,.284,.135,.049),lambda:h.diary_text.toPlainText().split('\n')[0][:14] or '写下今天的日记',size=21)
        self.mask((.405,.392,.24,.17));self.field(h.diary_text,(.406,.395,.236,.165))
        self.mask((.547,.902,.313,.047),'#FBFAF1');self.field(h.diary_note,(.552,.905,.303,.040))
        self.button('save','保存日记',(.87,.901,.104,.051),h.save_diary)
        self.button('diary-more','本地/AI日记与导出',(.406,.94,.232,.032),lambda:h.show_classic(6),True)
        self.label((.758,.284,.19,.045),lambda:'游戏心情：'+h.engine.mood,size=19)
        self.button('diary-album','打开相册',(.66,.365,.29,.30),lambda:self.show_page('album'))
    def backpack(self):
        h=self.host;e=h.engine
        ids=('fish','food','wet_food','freeze_dried',None,'happy_snack','bed','bowl','hammock','wand','brush',None)
        for i,item in enumerate(ids):
            row,col=divmod(i,3);x=.324+col*.212;y=.430+row*.146
            self.label((x,y,.063,.026),lambda item=item:'× '+str(e.data['inventory'].get(item,0)) if item else '待适配',size=18)
            if item:
                button=self.button('use-'+item,'摆放 / 使用 '+BY_ID[item]['name'],(x-.006,y+.030,.068,.040),lambda item=item:h.place_or_use(item))
                button.disabled_label='无库存'
                self.live.append((button,lambda item=item:e.data['inventory'].get(item,0)>0))
                box=(.195+col*.212,.400+row*.146,.126,.105);self.drag_rects[item]=box
            else:
                button=self.button('unavailable-'+str(i),'待适配',(x-.006,y+.030,.068,.040),lambda:None,True);button.setEnabled(False)
        for i in range(3):self.button('category'+str(i),'查看全部物件分类',(.168+i*.140,.300,.136,.054),lambda:h.show_classic(3))
        self.button('full-bag','全部物件 / 商城',(.862,.355,.121,.045),lambda:h.show_classic(3),True)
    def album(self):
        h=self.host;a=h.album_widget
        self.button('import','导入照片',(.78,.258,.19,.046),a.choose_files,True)
        self.label((.19,.274,.32,.025),lambda:a.status.text().split('\n')[0],size=17)
        for i,category in enumerate(('', '日常','午睡','玩耍')):
            self.button('album-filter'+str(i),'相册分类 '+(category or '全部'),(.202+i*.081,.260,.076,.047),lambda category=category:self.album_filter(category))
        self.button('album-sort','改变照片排序',(.815,.256,.145,.05),lambda:a.order.setCurrentIndex(1-a.order.currentIndex()))
        self.album_slots=[]
        for i in range(6):
            row,col=divmod(i,3);x=.211+col*.264;y=.348+row*.309
            self.album_slots.append((x,y,.220,.206))
            self.label((x,y+.208,.217,.062),lambda i=i:self.album_caption(i),size=16)
            self.button('photo'+str(i),'查看照片或导入',(.205+col*.264,.33+row*.309,.228,.25),lambda i=i:self.album_click(i))
        self.button('album-all','全部照片与日期筛选',(.68,.948,.29,.032),lambda:h.show_classic(8),True)
    def album_filter(self,category):
        combo=self.host.album_widget.category;combo.setCurrentIndex(max(0,combo.findData(category)))
    def album_caption(self,i):
        if i<len(self.album_ids):
            v=self.host.album_widget.store.get(self.album_ids[i]);return v['day']+' · '+v['category']+'\n'+v['title'] if v else ''
        return '年糕插画封面 · 非上传照片\n点击添加你自己的照片'
    def album_click(self,i):
        a=self.host.album_widget
        a.open_photo(self.album_ids[i]) if i<len(self.album_ids) else a.choose_files()
    def settings(self):
        h=self.host;p=h.engine.data['profile']
        self.label((.617,.177,.256,.026),lambda:p.get('display_name','年糕'),size=19)
        for key,y in (('personality',.221),('habits',.269),('likes',.317),('owner_name',.364)):
            self.mask((.613,y,.263,.036),'#FBF9F0');self.field(h.profile_fields[key],(.616,y+.002,.251,.031))
        self.button('profile-save','保存年糕档案',(.893,.343,.073,.043),h.save_profile)
        for name,box,callback,getter in (('topmost',(.519,.506,.036,.035),h.pet.toggle_top,lambda:h.pet.settings.data['always_on_top']),('idle',(.519,.562,.036,.035),lambda:h.pet.set_work_mode(not h.pet.work_mode),lambda:h.pet.work_mode)):
            button=self.button(name,name,box,callback);button.switch=True;button.setCheckable(True);self.checks.append((button,getter))
        self.mask((.774,.504,.166,.044),'#FAF6E8')
        slider=QSlider(Qt.Orientation.Horizontal);slider.setStyleSheet('QSlider::groove:horizontal{height:11px;background:#CFD3BD;border-radius:5px;}QSlider::sub-page:horizontal{background:#6C8555;border-radius:5px;}QSlider::handle:horizontal{background:#FCFAF0;border:1px solid #A4AA8D;width:24px;margin:-7px 0;border-radius:12px;}');slider.setRange(30,100);slider.setValue(round(h.pet.windowOpacity()*100));slider.valueChanged.connect(lambda v:h.pet.setWindowOpacity(v/100));self.embed(slider,(.777,.51,.16,.03))
        self.label((.942,.51,.032,.03),lambda:str(round(h.pet.windowOpacity()*100))+'%',size=18)
        for i,width in enumerate((160,240,330)):
            button=self.button('size'+str(i),('小','中','大')[i],(.776+i*.057,.56,.049,.039),lambda width=width:h.pet.resize_pet(width),True);button.setCheckable(True)
            self.checks.append((button,lambda width=width:min((160,240,330),key=lambda v:abs(v-h.pet.width()))==width))
        for key,y in (('sound',.704),('reminders',.757)):
            button=self.button(key,key,(.52,y,.035,.034),lambda key=key:h.interaction_pref(key,not h.engine.data['preferences'][key]));button.switch=True;button.setCheckable(True);self.checks.append((button,lambda key=key:h.engine.data['preferences'][key]))
        # Existing application has no all-data backup/delete operations. Do not imitate them.
        self.mask((.435,.879,.522,.045));self.label((.435,.879,.522,.045),lambda:'完整设置保留 API、密钥、Token、生日、音效与本地数据操作。',size=18)
        for i,label in enumerate(('API / Token','完整档案设置','相册与历史')):
            self.button('setting-more'+str(i),label,(.475+i*.184,.931,.10,.039),lambda i=i:h.show_classic(7 if i<2 else 8),True)
    def status(self):
        h=self.host;e=h.engine
        for i,key in enumerate(('mood','satiety','energy','health')):
            self.meter(key,(.458+i*.135,.285,.105,.182),True)
        self.mask((.864,.477,.075,.048));self.label((.867,.48,.069,.042),lambda:'健康',size=24)
        self.label((.85,.515,.10,.030),lambda:'虚拟健康状态',size=17)
        self.label((.469,.51,.10,.030),lambda:'当前心情：'+e.mood,size=17)
        self.label((.605,.51,.10,.030),lambda:'游戏饱腹数值',size=17)
        self.label((.739,.51,.10,.030),lambda:'游戏精力数值',size=17)
        for key,x in (('cleanliness',.649),('health',.901)):
            self.label((x,.588,.078 if key=='health' else .040,.035),lambda key=key:str(round(e.data['stats'][key]))+'%',size=25)
        self.meter('cleanliness',(.515,.625,.168,.019));self.meter('health',(.794,.625,.165,.019))
        self.label((.515,.650,.17,.03),lambda:'游戏清洁状态',size=17);self.label((.795,.650,.17,.03),lambda:'游戏健康状态',size=17)
        self.label((.244,.762,.16,.036),lambda:e.data['birth_date']+' · '+e.age()['text'],size=16)
        self.label((.244,.806,.16,.029),lambda:'未填写',size=17)
        self.label((.244,.845,.16,.032),lambda:e.data['profile'].get('personality') or '性格尚未填写',size=17)
        self.mask((.44,.787,.304,.155));self.label((.44,.787,.304,.155),lambda:'\n'.join(v['at'][11:16]+' '+v['text'] for v in e.data['events'] if v['day']==e.today().isoformat())[-600:] or '今天还没有记录，和年糕一起度过一会儿吧。',size=17)
        self.mask((.795,.79,.155,.15));self.label((.795,.79,.155,.15),lambda:'当前心情：'+e.mood+'\n今天的陪伴事件会记录在左侧。',size=19)
    def refresh(self):
        if self.page is None:return
        for widget,getter in self.live:
            value=getter()
            if isinstance(widget,QPushButton):widget.setEnabled(bool(value))
            else:widget.setText(str(value))
        for button,getter in self.checks:button.setChecked(bool(getter()))
        if self.page=='album' and self.host.album_widget.store:
            a=self.host.album_widget;records,_=a.store.query(a.month.currentData() or '',a.category.currentData() or '',a.search.text(),a.offset,6,bool(a.order.currentData()))
            ids=[v['id'] for v in records]
            if ids!=self.album_ids:
                for item in getattr(self,'album_images',[]):self.scene().removeItem(item)
                self.album_images=[];self.album_ids=ids
                for i,v in enumerate(records):
                    pix=QPixmap(str(a.store.owned(v['thumbnail'])));box=rect(self.album_slots[i]);pix=pix.scaled(box.size().toSize(),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
                    paper=self.scene().addRect(box,QPen(Qt.PenStyle.NoPen),QColor('#FAF6E8'));paper.setZValue(2);self.album_images.append(paper)
                    item=self.scene().addPixmap(pix);item.setPos(box.center()-QPointF(pix.width()/2,pix.height()/2));item.setZValue(2.1);self.album_images.append(item)
