import sys, time, math, random, json
from PySide6.QtCore import Qt,QTimer,QPoint,QSize
from PySide6.QtGui import QPainter,QRegion,QIcon,QCursor,QAction
from PySide6.QtWidgets import QWidget,QApplication,QMenu,QSystemTrayIcon
from .geometry import Rect,clamp_position,nearest_area
from .config import Settings
from .art import CatArt
from .behaviour import Behaviour
from .windows import WindowObstacles
from .bubble import SpeechBubble,PALETTE
from .dialogue import choose

MENU_STYLE="""
QMenu {background:#EFF6F1;color:#305E63;border:1px solid #8CCCCA;padding:8px;font:14px 'Microsoft YaHei';}
QMenu::item {padding:9px 28px 9px 16px;margin:2px;border-radius:7px;}
QMenu::item:selected {background:#8CCCCA;color:#305E63;}
QMenu::separator {height:1px;background:#899F84;margin:6px 12px;}
"""
class PetWindow(QWidget):
    def __init__(self,settings=None,probe=None):
        self.settings=settings or Settings()
        flags=Qt.WindowType.FramelessWindowHint|Qt.WindowType.Tool
        if self.settings.data["always_on_top"]:flags|=Qt.WindowType.WindowStaysOnTopHint
        super().__init__(None,flags)
        self.setWindowTitle("年糕 · 照片桌宠")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        from .life.engine import LifeEngine
        self.life=LifeEngine(self.settings.path.parent/"life.json");self.life_window=None
        self.art=CatArt();self.behaviour=Behaviour();self.observer=WindowObstacles()
        self.bubble=SpeechBubble();self.obstacles=[];self.dragging=False;self.pressed=False;self.menu_open=False
        self.press_global=QPoint();self.drag_offset=QPoint();self.float_pos=(0.0,0.0)
        self.last_tick=time.monotonic();self.started=self.last_tick;self.last_edges=0;self.last_poll=0;self.last_speech=self.started
        self.probe=probe;self.counts={"clicked":0,"dragged":0,"head_pet":0,"fed":0}
        self.pixmap=None;self.last_art_key=None;self.tray=None
        self.resize_pet(self.settings.data["width"],save=False)
        area=self.areas()[0];saved=self.settings.data["position"]
        x,y=saved if saved else (area.right-self.width()-24,area.bottom-self.height()-20)
        area=nearest_area(x,y,self.areas());self.float_pos=clamp_position(x,y,self.width(),self.height(),area)
        self.move(round(self.float_pos[0]),round(self.float_pos[1]));self.render_frame()
        self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(33)
        self.build_tray()
        app=QApplication.instance();app.screenAdded.connect(lambda _s:self.repair_position());app.screenRemoved.connect(lambda _s:self.repair_position())
        QTimer.singleShot(650,lambda:self.say("greet"))

    def pose_state(self,state):
        key=("walk_left" if self.behaviour.facing_left else "walk") if state in ("walk","perch","play") else state
        return self.art.ensure(key)
    def perform_action(self,action,duration=5):
        available=self.art.ensure(action)
        if available!=action and action not in ("walk","idle","sleep"):return False
        self.behaviour.action(action,None if action=="sleep" else duration);self.render_frame();return True
    def open_life(self):
        if self.life_window is None:
            from .life.window import LifeWindow
            self.life_window=LifeWindow(self)
        self.life_window.show();self.life_window.raise_();self.life_window.activateWindow()
    def areas(self):
        result=[]
        for screen in QApplication.screens():
            r=screen.availableGeometry();result.append(Rect(r.x(),r.y(),r.width(),r.height()))
        return result
    def rect_global(self):return Rect(self.x(),self.y(),self.width(),self.height())
    def screen_maps(self):
        return [{"name":s.name(),"origin":(s.geometry().x(),s.geometry().y()),"scale":s.devicePixelRatio()} for s in QApplication.screens()]
    def save(self):
        self.settings.data["position"]=[self.x(),self.y()]
        self.settings.save()
    def repair_position(self):
        area=nearest_area(self.x(),self.y(),self.areas())
        if self.width()>area.w-24 or self.height()>area.h-24:
            self.resize_pet(max(80,min(self.width(),area.w-24,(area.h-24)/1.3)),save=False)
        self.float_pos=clamp_position(self.x(),self.y(),self.width(),self.height(),area)
        self.move(round(self.float_pos[0]),round(self.float_pos[1]))
    def resize_pet(self,width,save=True):
        old_center=self.geometry().center();bottom=self.geometry().bottom()
        area=nearest_area(self.x(),self.y(),self.areas())
        width=int(max(80,min(420,width,area.w-24,(area.h-24)/1.3)))
        self.resize(width,self.height_for(width))
        self.settings.data["width"]=width
        self.last_art_key=None
        if hasattr(self,"art"):
            self.move(old_center.x()-width//2,bottom-self.height())
            self.repair_position();self.render_frame()
        if save:self.save()
    def height_for(self,width):
        state=self.behaviour.state
        art_state=self.pose_state(state)
        ratio=max(frame.height()/frame.width() for frame in self.art.frames[art_state])
        return max(50,int((width-16)*ratio+16))
    def render_frame(self):
        wanted_height=self.height_for(self.width())
        if self.height()!=wanted_height:
            bottom=self.y()+self.height()
            self.resize(self.width(),wanted_height)
            self.move(self.x(),bottom-wanted_height)
            self.float_pos=(float(self.x()),float(self.y()))
        state=self.behaviour.state
        phase=time.monotonic()-self.started
        frame=int(phase*(5 if state in ("walk","perch","play") else 3))%4 if state in ("walk","perch","play","pet","feed","groom","stretch","play_bow","yawn") else 0
        bob=int(round(math.sin(phase*(7 if state in ["pet","feed"] else 2))*1.5))
        art_state=self.pose_state(state)
        key=(art_state,frame,self.width(),self.height(),bob)
        if key==self.last_art_key:return
        self.last_art_key=key
        self.pixmap,mask=self.art.render(art_state,frame,self.width(),self.height(),bob)
        self.setMask(QRegion(mask))
        self.update()
    def tick(self):
        now=time.monotonic();dt=now-self.last_tick;self.last_tick=now
        if now-self.last_poll>=1:
            self.last_poll=now
            months=self.life.age()["effective_months"];activity=self.life.data["preferences"]["activity"]
            self.behaviour.speed=(42 if months>=84 else 48 if months<3 else 66 if months<12 else 58)*(.4+activity/100)
            for message in self.life.tick(self.behaviour.state=="sleep"):
                self.bubble.speak(message,self.rect_global(),self.areas())
            self.obstacles=self.observer.query(self.screen_maps())
            if not self.dragging:self.repair_position()
        if not self.dragging and not self.pressed and not self.menu_open:
            area=nearest_area(self.x(),self.y(),self.areas())
            self.float_pos=self.behaviour.tick(*self.float_pos,self.width(),self.height(),area,self.obstacles,dt,self.settings.data["roaming"] and self.life.data["preferences"]["activity"]>0)
            self.move(round(self.float_pos[0]),round(self.float_pos[1]))
            if self.behaviour.edge_contact and now-self.last_edges>8:
                self.last_edges=now;self.say("edge")
        if now-self.last_speech>random.uniform(18,28) and self.behaviour.state!="sleep" and not self.menu_open:
            self.say("idle")
        self.render_frame()
        if self.bubble.isVisible():self.bubble.place(self.rect_global(),self.areas())
        if self.probe:
            self.probe.write_text(json.dumps({"position":[self.x(),self.y()],"size":[self.width(),self.height()],"state":self.behaviour.state,"obstacles":len(self.obstacles),"native_obstacles":self.observer.supported,"counts":self.counts,"masked":not self.mask().isEmpty(),"bubble_visible":self.bubble.isVisible(),"bubble":[self.bubble.x(),self.bubble.y(),self.bubble.width(),self.bubble.height()],"provider_error":self.observer.last_error}),encoding="utf-8")
    def say(self,kind):
        self.last_speech=time.monotonic();self.bubble.speak(choose(kind),self.rect_global(),self.areas())
    def pet_head(self):
        self.life.care("pet");self.counts["head_pet"]+=1;self.behaviour.action("pet",4);self.say("pet")
    def feed(self):
        self.life.care("meal");self.counts["fed"]+=1;self.behaviour.action("feed",5);self.say("feed")
    def toggle_sleep(self):
        if self.behaviour.state=="sleep":self.behaviour.wake();self.say("wake")
        else:self.behaviour.action("sleep");self.say("sleep")
        self.render_frame()
    def toggle_top(self):
        enabled=not self.settings.data["always_on_top"]
        self.settings.data["always_on_top"]=enabled
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint,enabled);self.show();self.save()
    def toggle_roaming(self):
        self.settings.data["roaming"]=not self.settings.data["roaming"];self.behaviour.wake();self.save()
    def show_menu(self,position):
        menu=QMenu(self);menu.setStyleSheet(MENU_STYLE)
        heading=menu.addAction("年糕  /  NIANGAO");heading.setEnabled(False)
        menu.addSeparator();menu.addAction("摸摸头",self.pet_head);menu.addAction("喂吃的",self.feed)
        menu.addAction("叫它起床" if self.behaviour.state=="sleep" else "让它睡觉",self.toggle_sleep)
        sizes=menu.addMenu("调整大小");sizes.setStyleSheet(MENU_STYLE)
        for text,width in [("小巧 · 160",160),("舒适 · 240",240),("蓬松 · 340",340)]:
            sizes.addAction(text,lambda checked=False,w=width:(self.resize_pet(w),self.say("resize")))
        menu.addSeparator()
        top=menu.addAction("置顶开关",self.toggle_top);top.setCheckable(True);top.setChecked(self.settings.data["always_on_top"])
        roam=menu.addAction("自由巡逻",self.toggle_roaming);roam.setCheckable(True);roam.setChecked(self.settings.data["roaming"])
        menu.addSeparator();menu.addAction("退出程序",self.close)
        menu.addAction("年糕生活馆 · 更多功能",self.open_life)
        self.menu_open=True
        try:menu.exec(position)
        finally:self.menu_open=False;menu.deleteLater()
    def build_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():return
        self.tray=QSystemTrayIcon(QIcon(str(__import__('niangao.art',fromlist=['asset_path']).asset_path('niangao-idle.png'))),self)
        self.tray.setToolTip("年糕 · 右键猫咪可以互动")
        menu=QMenu();menu.setStyleSheet(MENU_STYLE)
        menu.addAction("年糕在哪里？",lambda:(self.show(),self.repair_position(),self.raise_(),self.say("greet")))
        menu.addAction("摸摸头",self.pet_head);menu.addAction("喂吃的",self.feed);menu.addAction("睡觉 / 起床",self.toggle_sleep)
        menu.addSeparator();menu.addAction("退出程序",self.close)
        menu.addAction("年糕生活馆 · 更多功能",self.open_life)
        self.tray.setContextMenu(menu);self.tray_menu=menu
        self.tray.show()
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            self.pressed=True;self.press_global=event.globalPosition().toPoint();self.drag_offset=self.press_global-self.pos();event.accept()
        elif event.button()==Qt.MouseButton.RightButton:self.show_menu(event.globalPosition().toPoint())
    def mouseMoveEvent(self,event):
        if self.pressed:
            point=event.globalPosition().toPoint()
            if not self.dragging and (point-self.press_global).manhattanLength()>4:
                self.dragging=True;self.say("drag")
            if self.dragging:
                self.move(point-self.drag_offset);self.float_pos=(float(self.x()),float(self.y()))
    def mouseReleaseEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton and self.pressed:
            was_dragging=self.dragging;self.pressed=False;self.dragging=False
            if was_dragging:self.counts["dragged"]+=1;self.behaviour.action("idle",2);self.repair_position();self.save()
            else:self.counts["clicked"]+=1;self.pet_head()
    def wheelEvent(self,event):
        delta=event.angleDelta().y()
        if delta:self.resize_pet(self.width()*(1.09 if delta>0 else 1/1.09));self.say("resize")
        event.accept()
    def paintEvent(self,event):
        if self.pixmap:
            p=QPainter(self);p.drawPixmap(0,0,self.pixmap);p.end()
    def closeEvent(self,event):
        self.timer.stop();self.save();self.life.focus_pause();self.life.save();self.bubble.close()
        if self.life_window:self.life_window.shutdown()
        if self.tray:self.tray.hide()
        event.accept();QApplication.instance().quit()
