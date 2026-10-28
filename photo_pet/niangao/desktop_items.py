"""Owned transparent desktop props; never creates files on the user's desktop."""
import math,time,uuid
from PySide6.QtCore import Qt,QPoint,QTimer,QRectF,QObject,Signal
from PySide6.QtGui import QPainter,QColor,QPen,QRegion,QFont
from PySide6.QtWidgets import QWidget,QMenu,QApplication,QFrame,QVBoxLayout,QLabel,QPushButton
from .geometry import Rect,nearest_area,clamp_position
from .life.catalog import BY_ID,is_placeable
from .life.item_art import item_pixmap
WATER={"water_bowl","water_fountain"}
CARE_OBJECT={"food_bowl":("meal","feed"),"bowl":("meal","feed"),"water_bowl":("water","feed"),"water_fountain":("water","feed"),
 "brush":("brush","groom"),"wash_basin":("bath","groom"),"litter":("litter","idle"),"bed":("rest","sleep"),
 "scratcher":("play","scratch"),"tree":("play","swat"),"hammock":("rest","sleep"),"rug":("rest","idle"),
 "health_kit":("checkup","expectant"),"plant":("pet","expectant"),"lamp":("rest","bored")}
class DesktopItem(QWidget):
    def __init__(self,manager,record):
        super().__init__(None,Qt.WindowType.Tool|Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint)
        self.manager=manager;self.record=record;self.uid=record["uid"];self.id=record["item"]
        self.setWindowTitle("年糕物件 · "+self.uid);self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        width=int(record.get("width",112));self.resize(width,width+26);self.down=False;self.dragged=False;self.offset=QPoint()
        self.setToolTip(BY_ID[self.id]["name"]+" · 左键拖动，轻点使用，右键补水或收回")
        self.phase=0.;self.last_time=time.monotonic();self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(80 if self.id in WATER else 500)
        self.repair();self.rebuild_mask()
    def repair(self):
        area=nearest_area(self.record["x"],self.record["y"],self.manager.pet.areas())
        x,y=clamp_position(self.record["x"],self.record["y"],self.width(),self.height(),area)
        self.move(round(x),round(y));self.record["x"],self.record["y"]=round(x),round(y)
    def rebuild_mask(self):
        pix=self.compose();self.setMask(QRegion(pix.mask()));self.update()
    def compose(self):
        from PySide6.QtGui import QPixmap
        pix=QPixmap(self.size());pix.fill(Qt.GlobalColor.transparent);p=QPainter(pix);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.drawPixmap(0,0,item_pixmap(self.id,self.width(),self.record.get("water",100)<=0))
        if self.id in WATER:
            level=int(self.record.get("water",100))
            p.setPen(QPen(QColor("#73b9cb"),1.5))
            if level>0:
                cx,cy=self.width()*.5,self.width()*.52;radius=5+(math.sin(self.phase*2.3)+1)*4
                p.drawEllipse(QRectF(cx-radius,cy-radius*.3,radius*2,radius*.6))
                if self.id=="water_fountain":
                    x=self.width()*.635;y=self.width()*(.24+.12*((self.phase*1.8)%1))
                    p.setBrush(QColor("#95d2df"));p.drawEllipse(QRectF(x,y,3,5))
            p.setPen(QColor("#342d2b"));p.setFont(QFont("Microsoft YaHei",8));p.drawText(QRectF(0,self.width()-14,self.width(),16),Qt.AlignmentFlag.AlignCenter,str(level)+"%")
        p.setPen(QPen(QColor("#342d2b"),1.5));p.setBrush(QColor("#fffaf0"));p.drawRoundedRect(QRectF(4,self.width()+1,self.width()-8,22),8,8)
        p.setFont(QFont("Microsoft YaHei",8));name=p.fontMetrics().elidedText(BY_ID[self.id]["name"],Qt.TextElideMode.ElideRight,self.width()-16)
        p.drawText(QRectF(8,self.width()+2,self.width()-16,20),Qt.AlignmentFlag.AlignCenter,name);p.end();return pix
    def tick(self):
        now=time.monotonic();self.phase+=min(.3,max(0,now-self.last_time));self.last_time=now
        if self.id in WATER and self.record.get("water",100)>0:self.update()
    def paintEvent(self,event):
        p=QPainter(self);p.drawPixmap(0,0,self.compose());p.end()
    def mousePressEvent(self,event):
        self.manager.pet.autonomy.click()
        if event.button()==Qt.MouseButton.LeftButton:
            self.down=True;self.dragged=False;self.press=event.globalPosition().toPoint();self.offset=self.press-self.pos();event.accept()
        elif event.button()==Qt.MouseButton.RightButton:
            menu=QMenu();menu.setStyleSheet("QMenu{background:#fffaf0;color:#342d2b;padding:8px;} QMenu::item{padding:8px 14px;}")
            menu.addAction("使用 / 和年糕互动",lambda:self.manager.activate(self.uid))
            if self.id in WATER:menu.addAction("加满清水",lambda:self.manager.refill(self.uid))
            menu.addAction("收回背包",lambda:self.manager.remove(self.uid));menu.addAction("一键清理桌面摆件",self.manager.clear)
            menu.exec(event.globalPosition().toPoint());menu.deleteLater()
    def mouseMoveEvent(self,event):
        if self.down:
            point=event.globalPosition().toPoint()
            if (point-self.press).manhattanLength()>4:self.dragged=True
            if self.dragged:self.move(point-self.offset)
    def mouseReleaseEvent(self,event):
        if self.down and event.button()==Qt.MouseButton.LeftButton:
            self.down=False
            if self.dragged:
                self.record.update(x=self.x(),y=self.y());self.repair();self.manager.save()
            else:self.manager.activate(self.uid)
    def closeEvent(self,event):
        self.timer.stop()
        if not self.manager.closing:self.manager.remove(self.uid,close=False)
        event.accept()

class DesktopItems(QObject):
    changed=Signal()
    def __init__(self,pet):
        super().__init__(pet);self.pet=pet;self.engine=pet.life;self.widgets={};self.closing=False
        accepted=[]
        for record in self.engine.data["desktop_items"]:
            id=record["item"]
            if record["uid"] in self.widgets or not is_placeable(id):continue
            if sum(v["item"]==id for v in accepted)>=self.engine.data["inventory"].get(id,0):continue
            accepted.append(record);self._show(record)
        self.engine.data["desktop_items"]=accepted
    def _show(self,record):
        w=DesktopItem(self,record);self.widgets[record["uid"]]=w;w.show();QTimer.singleShot(0,w.repair)
    def available(self,id):
        return max(0,self.engine.data["inventory"].get(id,0)-sum(v["item"]==id for v in self.engine.data["desktop_items"]))
    def place(self,id,point=None):
        if not is_placeable(id):return False,"该物品暂不能摆到桌面"
        if self.available(id)<1:return False,"这件物品已全部摆出，先收回一件吧"
        if len(self.widgets)>=32:return False,"桌面最多摆 32 件，请先一键收回"
        if point is None:point=QPoint(self.pet.x()+self.pet.width()+8,self.pet.y()+max(0,self.pet.height()-136))
        area=nearest_area(point.x(),point.y(),self.pet.areas());x,y=clamp_position(point.x()-56,point.y()-40,112,138,area)
        if any(Rect(x,y,112,138).intersects(Rect(w.x(),w.y(),w.width(),w.height())) for w in self.widgets.values()):
            found=False
            for shift in range(1,40):
                nx,ny=clamp_position(x+(shift%7)*125,y-(shift//7)*145,112,138,area)
                if not any(Rect(nx,ny,112,138).intersects(Rect(w.x(),w.y(),w.width(),w.height())) for w in self.widgets.values()):x,y=nx,ny;found=True;break
            if not found:return False,"附近没有空位，请拖到另一处或先清理"
        record=dict(uid=uuid.uuid4().hex,item=id,x=round(x),y=round(y),width=112,water=100)
        self.engine.data["desktop_items"].append(record);self._show(record);self.save()
        return True,"已摆放 "+BY_ID[id]["name"]+"，轻点使用，右键可收回"
    def save(self):self.engine.save();self.changed.emit()
    def remove(self,uid,close=True):
        widget=self.widgets.pop(uid,None);self.engine.data["desktop_items"][:]=[v for v in self.engine.data["desktop_items"] if v["uid"]!=uid]
        if widget and close:
            old=self.closing;self.closing=True;widget.close();widget.deleteLater();self.closing=old
        self.save()
    def clear(self):
        self.closing=True
        for widget in list(self.widgets.values()):widget.close();widget.deleteLater()
        self.widgets.clear();self.engine.data["desktop_items"]=[];self.closing=False;self.save()
        self.speak("桌面收拾好啦，物品都回到背包。")
    def refill(self,uid):
        widget=self.widgets.get(uid)
        if widget and widget.id in WATER:
            widget.record["water"]=100;widget.rebuild_mask();self.engine.event("water_fill","给"+BY_ID[widget.id]["name"]+"加满清水");self.save();self.speak("清水加满，咕嘟咕嘟～")
    def activate(self,uid):
        widget=self.widgets.get(uid)
        if not widget:return False
        self.pet.autonomy.click();id=widget.id;kind=BY_ID[id]["kind"]
        if id in WATER and widget.record.get("water",0)<=0:self.speak("小碗空啦，右键选择加满清水吧。");return False
        if id in CARE_OBJECT:
            care,action=CARE_OBJECT[id];ok,text=self.engine.care(care)
            if ok:
                if id in WATER:widget.record["water"]=max(0,widget.record.get("water",100)-20);widget.rebuild_mask()
                if care=="meal":self.pet.director.feed(self.pet.play_step)
                else:self.pet.perform_action(action)
                widget.raise_()
        elif kind=="furniture":
            ok,text=self.engine.care("pet")
            if ok:self.pet.perform_action("expectant")
        else:
            ok,text=self.engine.use(id)
            if ok:
                self.pet.perform_action("chew_toy" if kind=="toy" else "feed" if kind=="consumable" else "expectant")
                if kind!="toy":self.remove(uid)
        self.save();self.speak(text);return ok
    def speak(self,text):self.pet.bubble.speak(text,self.pet.rect_global(),self.pet.areas())
    def repair(self):
        for w in self.widgets.values():
            if not w.down:w.repair()
    def obstacles(self):return [Rect(w.x(),w.y(),w.width(),w.height()) for w in self.widgets.values()]
    def shutdown(self):
        self.closing=True
        for w in list(self.widgets.values()):
            w.record.update(x=w.x(),y=w.y());w.close()
        self.engine.save()

class ItemDragCard(QFrame):
    """Normal Qt mouse capture for owned-card drag; no Explorer file drag or global hook."""
    def __init__(self,id,pet,host,action_text=None,callback=None):
        super().__init__();self.id=id;self.pet=pet;self.host=host;self.start=None;self.ghost=None;self.cancelled=False
        self.setObjectName("itemCard");self.setFocusPolicy(Qt.FocusPolicy.StrongFocus);self.setMinimumWidth(145)
        layout=QVBoxLayout(self);layout.setContentsMargins(10,8,10,8)
        self.picture=QLabel();self.picture.setAlignment(Qt.AlignmentFlag.AlignCenter);self.picture.setPixmap(item_pixmap(id,100));self.picture.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents);layout.addWidget(self.picture)
        self.name=QLabel(BY_ID[id]["name"]);self.name.setAlignment(Qt.AlignmentFlag.AlignCenter);self.name.setWordWrap(True);self.name.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents);layout.addWidget(self.name)
        self.detail=QLabel();self.detail.setAlignment(Qt.AlignmentFlag.AlignCenter);self.detail.setWordWrap(True);self.detail.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents);layout.addWidget(self.detail)
        if action_text:
            self.button=QPushButton(action_text);self.button.clicked.connect(lambda _checked=False:callback());layout.addWidget(self.button)
        self.setToolTip("按住图像拖到生活馆窗口外摆放；Esc 取消。"+BY_ID[id]["note"])
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            self.pet.autonomy.click();self.start=event.globalPosition().toPoint();self.cancelled=False;self.setFocus();self.grabMouse();
            if self.pet.probe:self.pet.drag_debug={"item":self.id,"press":[self.start.x(),self.start.y()]}
            event.accept()
    def mouseMoveEvent(self,event):
        if self.start is None or self.cancelled:return
        point=event.globalPosition().toPoint()
        if self.ghost is None and (point-self.start).manhattanLength()>6:
            if self.pet.desktop.available(self.id)<1 or not is_placeable(self.id):self.host.notice("请先购买 / 收回该物品再拖放");self.cancelled=True;return
            self.ghost=QLabel(None,Qt.WindowType.Tool|Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint|Qt.WindowType.WindowTransparentForInput)
            self.ghost.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground);self.ghost.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating);self.ghost.setPixmap(item_pixmap(self.id,88));self.ghost.show();self.grabMouse()
            if self.pet.probe:self.pet.drag_debug["ghost"]=True
        if self.ghost:self.ghost.move(point-QPoint(44,44))
    def mouseReleaseEvent(self,event):
        if event.button()!=Qt.MouseButton.LeftButton:return
        point=event.globalPosition().toPoint();dragged=self.ghost is not None
        self.clear_ghost();self.releaseMouse()
        if self.pet.probe:self.pet.drag_debug.update(release=[point.x(),point.y()],cancelled=self.cancelled,was_drag=dragged,inside=self.host.frameGeometry().contains(point))
        if dragged and not self.cancelled:
            if self.host.frameGeometry().contains(point):self.host.notice("把图像拖到生活馆窗口外，再松开鼠标")
            else:self.host.result(self.pet.desktop.place(self.id,point))
        self.start=None
    def keyPressEvent(self,event):
        if event.key()==Qt.Key.Key_Escape:self.cancelled=True;self.clear_ghost();self.releaseMouse();self.start=None;event.accept()
        else:super().keyPressEvent(event)
    def clear_ghost(self):
        if self.ghost:self.ghost.close();self.ghost.deleteLater();self.ghost=None
    def closeEvent(self,event):self.clear_ghost();self.releaseMouse();super().closeEvent(event)
