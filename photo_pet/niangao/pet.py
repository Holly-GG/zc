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
from .interaction.actions import ACTIONS
from .interaction.director import Director
from .interaction.audio import SoundPlayer
from .interaction.input_link import KeyboardActivity
from .interaction.autonomy import AutonomyPolicy
from .desktop_items import DesktopItems

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
        self.autonomy=AutonomyPolicy();self.director=Director();self.director.set_rate(self.autonomy.rate)
        self.behaviour.autonomous_rate=self.autonomy.rate;self.behaviour.deadline=self.behaviour.clock()+3/self.autonomy.rate
        self.audio=SoundPlayer(self.settings.path.parent/"audio-cache",self.life.data["preferences"])
        self.keyboard=KeyboardActivity();self.press_started=0;self.hold_fired=False;self.stroke_mode=False;self.poke_until=0
        self.motion_started=time.monotonic();self.last_motion="idle";self.cursor_target=None;self.cursor_mode=False
        self.setMouseTracking(True)
        self.bubble=SpeechBubble();self.obstacles=[];self.dragging=False;self.pressed=False;self.menu_open=False
        self.press_global=QPoint();self.drag_offset=QPoint();self.float_pos=(0.0,0.0)
        self.last_tick=time.monotonic();self.started=self.last_tick;self.last_edges=0;self.last_poll=0;self.last_speech=self.started;self.next_speech_at=self.started+random.uniform(18,28)/self.autonomy.rate;self.last_autonomy_rate=self.autonomy.rate
        self.probe=probe;self.counts={"clicked":0,"dragged":0,"head_pet":0,"fed":0}
        self.pixmap=None;self.last_art_key=None;self.tray=None
        self.resize_pet(self.settings.data["width"],save=False)
        area=self.areas()[0];saved=self.settings.data["position"]
        x,y=saved if saved else (area.right-self.width()-24,area.bottom-self.height()-20)
        area=nearest_area(x,y,self.areas());self.float_pos=clamp_position(x,y,self.width(),self.height(),area)
        self.move(round(self.float_pos[0]),round(self.float_pos[1]));self.render_frame()
        self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(33)
        self.desktop=DesktopItems(self)
        self.build_tray()
        app=QApplication.instance()
        from PySide6.QtCore import QObject,QEvent
        class ClickTracker(QObject):
            def __init__(self,policy,parent):super().__init__(parent);self.policy=policy
            def eventFilter(self,obj,event):
                if event.type()==QEvent.Type.MouseButtonPress:self.policy.click()
                return False
        self.click_tracker=ClickTracker(self.autonomy,self);app.installEventFilter(self.click_tracker)
        app.screenAdded.connect(lambda _s:self.repair_position());app.screenRemoved.connect(lambda _s:self.repair_position())
        QTimer.singleShot(650,lambda:self.say("greet"))

    def pose_state(self,state):
        key=("walk_left" if self.behaviour.facing_left else "walk") if state in ("walk","perch","play","elegant_walk") else state
        return self.art.ensure(ACTIONS[key].resource if key in ACTIONS else key)
    def perform_action(self,action,duration=5,interrupt=True):
        resource=ACTIONS[action].resource if action in ACTIONS else action
        available=self.art.ensure(resource)
        if available!=resource:return False
        if interrupt:self.director.cancel();self.cursor_target=None;self.cursor_mode=False
        self.behaviour.action(action,None if action=="sleep" else duration)
        if action in ("walk","elegant_walk"):
            area=nearest_area(self.x(),self.y(),self.areas())
            self.behaviour.target=clamp_position(random.uniform(area.x,area.right),random.uniform(area.y,area.bottom),self.width(),self.height(),area)
        self.motion_started=time.monotonic();self.last_motion=action
        info=ACTIONS.get(action)
        if info:
            sound=info.sound
            if sound in ("milk_meow","adult_meow","senior_meow"):
                age=self.life.age()["effective_months"];sound="milk_meow" if age<3 else "senior_meow" if age>=120 else "adult_meow"
            if sound:self.audio.play(sound)
        self.render_frame();return True
    def play_step(self,action,duration):return self.perform_action(action,duration,False)
    def tease(self):self.director.tease(self.play_step)
    def poke(self):
        self.poke_until=time.monotonic()+.5;self.director.poke(self.play_step);self.say("poke")
    def chase_cursor(self,force=False):
        point=QCursor.pos();distance=math.hypot(point.x()-self.geometry().center().x(),point.y()-self.geometry().center().y())
        if distance<=90 and not force:
            self.cursor_mode=False;self.cursor_target=None
            self.director.sequence([("rub_mouse",3),("tail_sway",2)],self.play_step);return True
        if not force and distance>=650:return False
        area=nearest_area(point.x(),point.y(),self.areas())
        self.cursor_target=clamp_position(point.x()-self.width()/2-35,point.y()-self.height()/2+40,self.width(),self.height(),area)
        self.cursor_mode=True;self.director.chase(self.play_step,random.random()<.35);return True
    def motion_interactions(self,now,dt):
        prefs=self.life.data["preferences"]
        rate=self.autonomy.rate
        if rate!=self.last_autonomy_rate:
            self.next_speech_at=now+max(0,self.next_speech_at-now)*self.last_autonomy_rate/rate
            if self.behaviour.state=="idle" and not self.director.active:self.behaviour.deadline=now+max(0,self.behaviour.deadline-now)*self.last_autonomy_rate/rate
            self.last_autonomy_rate=rate
        self.director.set_rate(rate);self.behaviour.autonomous_rate=rate
        self.director.tick(self.play_step,self.dragging or self.pressed or self.menu_open)
        if self.pressed and not self.dragging and not self.hold_fired and now-self.press_started>.85:
            self.hold_fired=True;self.director.sequence([("nibble",2.5)],self.play_step)
        if self.behaviour.state=="sleep":
            if self.director.ready("snore",22/self.autonomy.rate):self.audio.play("snore")
            return
        if self.dragging or self.pressed or self.menu_open:return
        if self.keyboard.poll(prefs["input_link"]) and self.director.ready("typing",4/self.autonomy.rate):
            self.cursor_mode=False;self.cursor_target=None
            self.director.sequence([(random.choice(["keyboard_paw","peek_screen","typing_nod"]),2.5)],self.play_step)
        if prefs["cursor_chase"] and not self.director.active and self.director.ready("cursor",9/self.autonomy.rate):self.chase_cursor()
        if self.cursor_mode and self.cursor_target and self.behaviour.state in ("stalk","pounce"):
            x,y=self.float_pos;tx,ty=self.cursor_target;dist=math.hypot(tx-x,ty-y);step=min(dist,(35 if self.behaviour.state=="stalk" else 170)*min(dt,.08))
            if dist>1:
                from .geometry import hits_edge
                nx,ny=x+(tx-x)*step/dist,y+(ty-y)*step/dist
                area=nearest_area(x,y,self.areas());nx,ny=clamp_position(nx,ny,self.width(),self.height(),area)
                if not hits_edge(self.rect_global(),Rect(nx,ny,self.width(),self.height()),self.obstacles):
                    self.float_pos=nx,ny;self.move(round(nx),round(ny))
        if not self.director.active:
            self.cursor_mode=False;self.cursor_target=None
        allowed=prefs["emotion_actions"] and self.settings.data["roaming"] and self.behaviour.state in ("idle","walk")
        self.director.auto(self.life.mood,self.play_step,allowed)
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
        if self.dragging:return self.height()
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
        art_state=self.pose_state(state)
        if state!=self.last_motion:self.motion_started=time.monotonic();self.last_motion=state
        elapsed=time.monotonic()-self.motion_started
        count=len(self.art.frames[art_state])
        frame=int(elapsed*(5 if state in ("walk","perch","play","elegant_walk") else 2.8))%count
        if state=="mouth_lick":frame=[2,3,3,2][int(elapsed*3)%4]
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
            self.obstacles=self.observer.query(self.screen_maps())+self.desktop.obstacles()
            self.desktop.repair()
            if not self.dragging:self.repair_position()
        if not self.dragging and not self.pressed and not self.menu_open:
            area=nearest_area(self.x(),self.y(),self.areas())
            self.float_pos=self.behaviour.tick(*self.float_pos,self.width(),self.height(),area,self.obstacles,dt,self.settings.data["roaming"] and self.life.data["preferences"]["activity"]>0)
            self.move(round(self.float_pos[0]),round(self.float_pos[1]))
            if self.behaviour.edge_contact and now-self.last_edges>8/self.autonomy.rate:
                self.last_edges=now;self.say("edge")
        if now>=self.next_speech_at and self.behaviour.state!="sleep" and not self.menu_open:
            self.say("idle")
        self.render_frame()
        self.motion_interactions(now,dt)
        if self.bubble.isVisible():self.bubble.place(self.rect_global(),self.areas())
        if self.probe:
            ui_probe=None
            if self.life_window and self.life_window.isVisible():
                ui=self.life_window;nav={}
                for i in range(ui.nav.count()):
                    point=ui.nav.viewport().mapToGlobal(ui.nav.visualItemRect(ui.nav.item(i)).center());nav[str(i)]=[point.x(),point.y()]
                cards={}
                for id,card in getattr(ui,"bag_cards",{}).items():
                    point=card.picture.mapToGlobal(card.picture.rect().center())
                    if card.isVisible() and ui.frameGeometry().contains(point):cards[id]=[point.x(),point.y()]
                clear=ui.clear_desktop_button.mapToGlobal(ui.clear_desktop_button.rect().center())
                ui_probe={"rect":[ui.x(),ui.y(),ui.width(),ui.height()],"dpi":ui.devicePixelRatioF(),"nav":nav,"bag_cards":cards,"clear":[clear.x(),clear.y()]}
            self.probe.write_text(json.dumps({"card_drag":getattr(self,"drag_debug",None),"dashboard":ui_probe,"desktop_props":[{"uid":w.uid,"item":w.id,"position":[w.x(),w.y()]} for w in self.desktop.widgets.values()],"position":[self.x(),self.y()],"size":[self.width(),self.height()],"state":self.behaviour.state,"obstacles":len(self.obstacles),"native_obstacles":self.observer.supported,"counts":self.counts,"masked":not self.mask().isEmpty(),"bubble_visible":self.bubble.isVisible(),"bubble":[self.bubble.x(),self.bubble.y(),self.bubble.width(),self.bubble.height()],"provider_error":self.observer.last_error}),encoding="utf-8")
    def say(self,kind):
        self.last_speech=time.monotonic();self.next_speech_at=self.last_speech+random.uniform(18,28)/self.autonomy.rate;self.bubble.speak(choose(kind),self.rect_global(),self.areas())
    def pet_head(self):
        self.life.care("pet");self.counts["head_pet"]+=1;self.director.stroke(self.play_step);self.say("pet")
    def feed(self):
        self.life.care("meal");self.counts["fed"]+=1;self.director.feed(self.play_step);self.say("feed")
    def toggle_sleep(self):
        self.director.cancel();self.cursor_mode=False;self.cursor_target=None
        if self.behaviour.state=="sleep":self.behaviour.wake();self.say("wake")
        else:self.perform_action("sleep");self.say("sleep")
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
        menu.addAction("一键清理桌面摆件",self.desktop.clear)
        menu.addAction("逗年糕玩",self.tease)
        menu.addAction("戳一下（也可双击）",self.poke)
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
        menu.addAction("一键清理桌面摆件",self.desktop.clear)
        menu.addAction("逗年糕玩",self.tease)
        menu.addAction("戳一下（也可双击）",self.poke)
        self.tray.setContextMenu(menu);self.tray_menu=menu
        self.tray.show()
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            self.pressed=True;self.press_started=time.monotonic();self.hold_fired=False;self.stroke_mode=bool(event.modifiers()&Qt.KeyboardModifier.ShiftModifier);self.press_global=event.globalPosition().toPoint();self.drag_offset=self.press_global-self.pos();event.accept()
        elif event.button()==Qt.MouseButton.RightButton:self.show_menu(event.globalPosition().toPoint())
    def mouseMoveEvent(self,event):
        if self.pressed:
            point=event.globalPosition().toPoint()
            if self.stroke_mode:
                if (point-self.press_global).manhattanLength()>3 and self.director.ready("stroke",1.5):self.director.stroke(self.play_step)
                return
            if not self.dragging and (point-self.press_global).manhattanLength()>4:
                self.dragging=True;self.director.cancel();self.cursor_mode=False;self.cursor_target=None
                self.perform_action(random.choice(["hang","struggle","fear_ball"]),8)
                self.say("drag")
            if self.dragging:
                self.move(point-self.drag_offset);self.float_pos=(float(self.x()),float(self.y()))
    def mouseReleaseEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton and self.pressed:
            was_dragging=self.dragging;self.pressed=False;self.dragging=False
            if was_dragging:self.counts["dragged"]+=1;self.behaviour.action("idle",2);self.repair_position();self.save()
            else:
                self.counts["clicked"]+=1
                if not self.hold_fired and not self.stroke_mode and time.monotonic()>self.poke_until:self.pet_head()
    def mouseDoubleClickEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            self.pressed=True;self.poke();event.accept()
    def wheelEvent(self,event):
        delta=event.angleDelta().y()
        if delta:self.resize_pet(self.width()*(1.09 if delta>0 else 1/1.09));self.say("resize")
        event.accept()
    def paintEvent(self,event):
        if self.pixmap:
            p=QPainter(self);p.drawPixmap(0,0,self.pixmap)
            if self.behaviour.state=="cursor_trophy":
                from PySide6.QtGui import QColor
                p.setPen(QColor("#305E63"));p.setBrush(QColor("#8CCCCA"))
                from PySide6.QtGui import QPolygon
                x,y=int(self.width()*.58),int(self.height()*.42)
                p.drawPolygon(QPolygon([QPoint(x,y),QPoint(x+5,y+16),QPoint(x+9,y+10),QPoint(x+17,y+9)]))
            p.end()
    def closeEvent(self,event):
        self.timer.stop();self.audio.stop();self.desktop.shutdown();self.save();self.life.focus_pause();self.life.save();self.bubble.close()
        if self.life_window:self.life_window.shutdown()
        if self.tray:self.tray.hide()
        event.accept();QApplication.instance().quit()
