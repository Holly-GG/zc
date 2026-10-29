"""Owned transparent desktop props; never creates files on the user's desktop."""
import math,time,uuid,random
from PySide6.QtCore import Qt,QPoint,QTimer,QRectF,QObject,Signal,QSize
from PySide6.QtGui import QPainter,QColor,QPen,QRegion,QFont
from PySide6.QtWidgets import QWidget,QMenu,QApplication,QFrame,QVBoxLayout,QBoxLayout,QLabel,QPushButton
from .geometry import Rect,nearest_area,clamp_position
from .life.catalog import BY_ID,is_placeable,desktop_width
from .prop_physics import Body,accepts
from .dialogue import choose
from .life.item_art import item_pixmap,illustrated_item_pixmap
from .desktop_routines import PACKETS,SMALL_FOOD,MEAL_BOWLS,DesktopRoutine
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
        width=int(record.get("width",112));self.resize(width,width+(0 if self.id in SMALL_FOOD else 26));self.down=False;self.dragged=False;self.offset=QPoint()
        self.setToolTip(BY_ID[self.id]["name"]+" · 左键拖动，轻点使用，右键补水或收回")
        if self.id in PACKETS:self.setToolTip("左键拖动；右键逐颗倒出；Shift + 右键打开菜单")
        if self.id=="litter":self.setToolTip("轻点邀请年糕使用；右键铲砂，砂团与清理状态会保存")
        self.body=Body(float(record["x"]),float(record["y"]),55 if self.id=="mouse" else 0);self.pinned=bool(record.get("pinned",False))
        self.phase=0.;self.last_time=time.monotonic();self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(33)
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
        p.save()
        if self.id in ("wand","feather") and not self.manager.pet.work_mode:
            p.translate(self.width()/2,self.width()*.78);p.rotate(math.sin(self.phase*2.1)*4);p.translate(-self.width()/2,-self.width()*.78)
        p.drawPixmap(0,0,item_pixmap(self.id,self.width(),(self.id in WATER and self.record.get("water",100)<=0) or (self.id in MEAL_BOWLS and self.record.get("servings",3)<=0)));p.restore()
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
        if self.id in MEAL_BOWLS:
            n=self.record.get("servings",3);p.setPen(QColor("#305e63"));p.setFont(QFont("Microsoft YaHei",8));p.drawText(QRectF(0,self.width()-16,self.width(),16),Qt.AlignmentFlag.AlignCenter,f"基础粮 {n}/3")
        if self.id=="litter":
            dirt=self.record.get("dirt",0)
            for i in range(dirt):
                p.setPen(QPen(QColor("#715443"),1));p.setBrush(QColor("#a48a6a"));p.drawEllipse(QRectF(self.width()*(.29+i*.17),self.width()*(.45+(i%2)*.04),9,6))
            p.setPen(QColor("#8f6650" if dirt else "#40a387"));p.setFont(QFont("Microsoft YaHei",8));p.drawText(QRectF(0,self.width()-16,self.width(),16),Qt.AlignmentFlag.AlignCenter,f"待铲砂 {dirt}/3" if dirt else "猫砂很干净")
        if self.id in SMALL_FOOD:p.end();return pix
        p.setPen(QPen(QColor("#342d2b"),1.5));p.setBrush(QColor("#fffaf0"));p.drawRoundedRect(QRectF(4,self.width()+1,self.width()-8,22),8,8)
        p.setFont(QFont("Microsoft YaHei",8));name=p.fontMetrics().elidedText(BY_ID[self.id]["name"]+(" · "+str(self.record.get("remaining",PACKETS[self.id][1])) if self.id in PACKETS else ""),Qt.TextElideMode.ElideRight,self.width()-16)
        p.drawText(QRectF(8,self.width()+2,self.width()-16,20),Qt.AlignmentFlag.AlignCenter,name);p.end();return pix
    def tick(self):
        now=time.monotonic();dt=max(0,now-self.last_time);self.phase+=min(.3,dt);self.last_time=now
        pet=self.manager.pet
        if not self.down and not self.pinned:
            area=nearest_area(self.x(),self.y(),pet.areas())
            surfaces=[Rect(w.x()+8,w.y()+w.width()*.25,w.width()-16,1) for w in self.manager.widgets.values() if w is not self and (w.pinned or w.body.grounded) and not w.down]
            # Only land on window top edges approached from above; never treat a whole app as a wall.
            surfaces+=getattr(self.manager,"window_surfaces",[])
            active=not pet.work_mode
            if self.id=="mouse":self.body.vx=(55 if self.body.vx>=0 else -55) if active else 0
            self.body.advance(dt,self.width(),self.height(),area,surfaces,self.id=="ball" and active,self.id=="mouse" and active,settle_bounce=self.id in SMALL_FOOD)
            self.move(round(self.body.x),round(self.body.y));self.record.update(x=self.x(),y=self.y())
        if self.id in ("wand","feather"):self.rebuild_mask()
        elif self.id in WATER or self.id=="laser":self.update()
        if self.id=="laser" and not pet.work_mode:
            self.manager.move_laser(self,now)
    def paintEvent(self,event):
        p=QPainter(self);p.drawPixmap(0,0,self.compose());p.end()
    def mousePressEvent(self,event):
        self.manager.pet.autonomy.click()
        if event.button()==Qt.MouseButton.LeftButton:
            self.down=True;self.dragged=False;self.press=event.globalPosition().toPoint();self.offset=self.press-self.pos();event.accept()
        elif event.button()==Qt.MouseButton.RightButton:
            if self.id in PACKETS and not (event.modifiers()&Qt.KeyboardModifier.ShiftModifier):self.manager.drop_piece(self.uid);return
            menu=QMenu();menu.setStyleSheet("QMenu{background:#fffaf0;color:#342d2b;padding:8px;} QMenu::item{padding:8px 14px;}")
            menu.addAction("使用 / 和年糕互动",lambda:self.manager.activate(self.uid))
            if self.id in MEAL_BOWLS:menu.addAction("补满基础粮（3份）",lambda:self.manager.refill_food(self.uid))
            if self.id=="litter":
                menu.addAction("铲砂清理",lambda:self.manager.clean_litter(self.uid))
            if self.id in WATER:menu.addAction("加满清水",lambda:self.manager.refill(self.uid))
            pin=menu.addAction("固定位置 / 恢复掉落",self.toggle_pin)
            menu.addAction("收回背包",lambda:self.manager.remove(self.uid));menu.addAction("一键清理桌面摆件",self.manager.clear)
            menu.exec(event.globalPosition().toPoint());menu.deleteLater()
    def toggle_pin(self):
        self.pinned=not self.pinned;self.record["pinned"]=self.pinned;self.body.vx=self.body.vy=0;self.manager.save()
    def mouseMoveEvent(self,event):
        if self.down:
            point=event.globalPosition().toPoint()
            if (point-self.press).manhattanLength()>4:self.dragged=True
            if self.dragged:self.move(point-self.offset)
    def mouseReleaseEvent(self,event):
        if self.down and event.button()==Qt.MouseButton.LeftButton:
            self.down=False
            if self.dragged:
                self.record.update(x=self.x(),y=self.y());self.repair();self.body=Body(float(self.x()),float(self.y()));self.manager.save()
            else:self.manager.activate(self.uid)
    def closeEvent(self,event):
        self.timer.stop()
        if not self.manager.closing:self.manager.remove(self.uid,close=False)
        event.accept()

class DesktopItems(QObject):
    changed=Signal()
    def __init__(self,pet):
        super().__init__(pet);self.pet=pet;self.engine=pet.life;self.widgets={};self.closing=False;self.window_surfaces=[];self.rng=random.Random();self.next_interest=time.monotonic()+15;self.laser_spots={};self.interest=None;self.last_interest_save=0
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
        width=desktop_width(id)
        x,y=clamp_position(point.x()-width/2,point.y()-40,width,width+26,area)
        record=dict(uid=uuid.uuid4().hex,item=id,x=round(x),y=round(y),width=width,water=100)
        if id in PACKETS:
            queue=self.packet_queue(id);record["remaining"]=queue.pop(0) if queue else PACKETS[id][1]
        self.engine.data["desktop_items"].append(record);self._show(record);self.save()
        return True,"已摆放 "+BY_ID[id]["name"]+"，轻点使用，右键可收回"
    def save(self):self.engine.save();self.changed.emit()
    def remove(self,uid,close=True):
        widget=self.widgets.pop(uid,None)
        if widget:self.return_partial(widget)
        spot=self.laser_spots.pop(uid,None)
        if spot:spot.close();spot.deleteLater()
        self.engine.data["desktop_items"][:]=[v for v in self.engine.data["desktop_items"] if v["uid"]!=uid]
        if widget and close:
            old=self.closing;self.closing=True;widget.close();widget.deleteLater();self.closing=old
        self.save()
    def clear(self):
        self.closing=True
        for widget in list(self.widgets.values()):
            self.return_partial(widget)
            widget.close();widget.deleteLater()
        for spot in self.laser_spots.values():spot.close();spot.deleteLater()
        self.laser_spots.clear()
        self.widgets.clear();self.engine.data["desktop_items"]=[];self.closing=False;self.save()
        self.speak("桌面收拾好啦，物品都回到背包。")
    def refill(self,uid):
        widget=self.widgets.get(uid)
        if widget and widget.id in WATER:
            widget.record["water"]=100;widget.rebuild_mask();self.engine.event("water_fill","给"+BY_ID[widget.id]["name"]+"加满清水");self.save();self.speak("清水加满，咕嘟咕嘟～")
    def activate(self,uid,manual=True):
        widget=self.widgets.get(uid)
        if not widget:return False
        if manual:self.pet.autonomy.click()
        id=widget.id;kind=BY_ID[id]["kind"]
        if id in WATER and widget.record.get("water",0)<=0:self.speak("小碗空啦，右键选择加满清水吧。");return False
        if id in PACKETS:return self.drop_piece(uid)
        if self.pet.work_mode and (kind=="consumable" or id in MEAL_BOWLS or id=="litter"):
            self.speak("工作模式先安静陪伴，退出后再走过去互动吧。");return False
        if id in MEAL_BOWLS and widget.record.get("servings",3)<=0:self.speak("粮碗空啦，右键补充基础粮吧。");return False
        if (kind in ("toy","consumable") or id in ("food_bowl","bowl")) and not accepts(self.engine.data["stats"],"consumable" if kind=="consumable" or id in ("food_bowl","bowl") else "toy",self.rng):
            self.speak(choose("refuse_food" if kind=="consumable" or id in ("food_bowl","bowl") else "refuse_toy"));return False
        if kind=="consumable" and BY_ID[id]["category"]=="食品" or id in MEAL_BOWLS or id=="litter":
            return self.start_routine(widget,"litter" if id=="litter" else "food")
        if id in ("tunnel","tree","hammock","bed","soft_bed","rug","blanket","garden_patch"):
            return self.start_furniture(widget)
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
                self.pet.perform_action({"wand":"swat","feather":"pounce","ball":"pounce","mouse":"stalk","bell_ball":"swat","catnip":"roll","laser":"stalk"}.get(id,"chew_toy" if kind=="toy" else "feed" if kind=="consumable" else "expectant"))
                if id in ("bell_ball","blanket"):
                    widget.body.vx=self.rng.choice([-1,1])*160;widget.body.vy=-160
                if kind=="toy" and self.engine.data["preferences"]["easter_eggs"] and self.rng.random()<.12:
                    widget.body.vx=self.rng.choice([-1,1])*190;widget.body.vy=-120;text=choose("prank")
                if kind!="toy":self.remove(uid)
        self.save();self.speak(text);return ok
    def packet_queue(self,id):
        return self.engine.data["freeze_packets"] if id=="freeze_dried" else self.engine.data["food_packets"][id]
    def return_partial(self,widget):
        if widget.id in PACKETS:
            remaining=widget.record.get("remaining",PACKETS[widget.id][1])
            if isinstance(remaining,int) and 0<remaining<PACKETS[widget.id][1]:self.packet_queue(widget.id).append(remaining)
    def drop_piece(self,uid):
        widget=self.widgets.get(uid)
        if not widget or widget.id not in PACKETS or len(self.widgets)>=32:return False
        piece_id,maximum=PACKETS[widget.id];remaining=widget.record.get("remaining",maximum)
        if not isinstance(remaining,int) or not 1<=remaining<=maximum:return False
        self.engine.data["inventory"][piece_id]=self.engine.data["inventory"].get(piece_id,0)+1
        record=dict(uid=uuid.uuid4().hex,item=piece_id,x=widget.x()+widget.width()*.8,y=widget.y()+widget.width()*.3,width=38,water=100)
        self.engine.data["desktop_items"].append(record);self._show(record)
        piece=self.widgets[record["uid"]];piece.body.vx=self.rng.uniform(45,105);piece.body.vy=-self.rng.uniform(70,140)
        widget.record["remaining"]=remaining-1
        if remaining==1:self.engine.data["inventory"][widget.id]-=1;self.remove(uid)
        else:widget.rebuild_mask()
        self.engine.event("drop_food",BY_ID[piece_id]["name"]+"掉落一颗");self.save();return True
    def refill_food(self,uid):
        widget=self.widgets.get(uid)
        if widget and widget.id in MEAL_BOWLS:
            widget.record["servings"]=3;widget.rebuild_mask();self.engine.event("food_fill","补满三份基础粮");self.save();self.speak("基础粮补满啦，等年糕慢慢吃。")
    def clean_litter(self,uid):
        widget=self.widgets.get(uid)
        if not widget or widget.id!="litter":return False
        if getattr(self.pet.furniture,"uid",None)==uid:self.pet.furniture.cancel()
        dirt=widget.record.get("dirt",0);widget.record["dirt"]=0;widget.rebuild_mask()
        if dirt:
            self.engine.data["stats"]["cleanliness"]=min(100,self.engine.data["stats"]["cleanliness"]+4)
            self.engine.event("litter_clean","清理了猫砂盆的砂团")
        self.save();self.speak("猫砂铲干净啦，小爪爪给你盖章。" if dirt else "已经很干净啦，不用重复铲砂。");return True
    def start_routine(self,widget,kind):
        current=self.pet.furniture
        if current and getattr(current,"uid",None)==widget.uid:self.speak("年糕正在这里忙，稍等一会儿呀。");return False
        if self.pet.work_mode:return False
        if widget.down or (not widget.pinned and abs(widget.body.vy)>20):self.speak("等它落稳，再让年糕走过去吧。");return False
        if kind=="litter" and widget.record.get("dirt",0)>=3:self.speak("猫砂盆需要铲一铲，右键就能清理。");return False
        if current:current.cancel()
        self.pet.furniture=DesktopRoutine(self.pet,widget,kind);self.speak(choose("litter" if kind=="litter" else "feed"));return True
    def status_rows(self):
        current=self.pet.furniture
        rows=[]
        for w in self.widgets.values():
            if w.id in MEAL_BOWLS:state=f"基础粮 {w.record.get('servings',3)}/3"
            elif w.id in WATER:state=f"清水 {w.record.get('water',100)}%"
            elif w.id=="litter":state=f"待铲砂 {w.record.get('dirt',0)}/3"
            elif w.id in PACKETS:state=f"剩余 {w.record.get('remaining',PACKETS[w.id][1])} 颗"
            else:continue
            if getattr(current,"uid",None)==w.uid:state+=' · '+current.phase
            rows.append(BY_ID[w.id]["name"]+'  /  '+state)
        return rows
    def start_furniture(self,widget):
        if self.pet.work_mode:self.speak("工作模式正在安静值班，退出后再玩家具吧。");return False
        if not accepts(self.engine.data["stats"],"toy",self.rng):self.speak(choose("refuse_toy"));return False
        from .furniture import FurnitureSession
        if getattr(self.pet,"furniture",None):self.pet.furniture.cancel()
        self.pet.furniture=FurnitureSession(self.pet,widget,self.rng)
        self.engine.event("furniture","靠近"+BY_ID[widget.id]["name"]+"互动");self.save();return True
    def move_laser(self,widget,now):
        from .furniture import LightSpot
        spot=self.laser_spots.get(widget.uid)
        if spot is None:spot=LightSpot();self.laser_spots[widget.uid]=spot
        area=nearest_area(widget.x(),widget.y(),self.pet.areas())
        x,y=clamp_position(widget.x()+math.sin(now*.8)*130,widget.y()-65+math.cos(now*1.1)*65,16,16,area)
        spot.move(round(x),round(y));spot.show()
    def tick_interest(self,now):
        if now-self.last_interest_save>5:
            self.last_interest_save=now;self.engine.save()
        if self.pet.work_mode:
            self.interest=None
            for spot in self.laser_spots.values():spot.hide()
            return
        if self.interest:
            uid,deadline=self.interest;widget=self.widgets.get(uid)
            if not widget or now>deadline or self.pet.dragging or self.pet.pressed or self.pet.menu_open:self.interest=None
            else:
                target=self.laser_spots.get(uid,widget);point=target.geometry().center()
                foot=QPoint(self.pet.x()+self.pet.width()//2,self.pet.y()+self.pet.height()-10)
                if (point-foot).manhattanLength()<85:
                    self.interest=None;self.activate(uid,False)
                else:
                    area=nearest_area(point.x(),point.y(),self.pet.areas())
                    self.pet.behaviour.target=clamp_position(point.x()-self.pet.width()/2,point.y()-self.pet.height()+20,self.pet.width(),self.pet.height(),area)
                return
        if now<self.next_interest or self.pet.dragging or self.pet.pressed or self.pet.menu_open or self.pet.director.active or getattr(self.pet,"furniture",None):return
        self.next_interest=now+self.rng.uniform(12,25)/self.pet.autonomy.rate
        candidates=[w for w in self.widgets.values() if not w.down and BY_ID[w.id]["kind"] in ("toy","consumable","furniture")]
        if not candidates:return
        widget=self.rng.choice(candidates)
        if not accepts(self.engine.data["stats"],BY_ID[widget.id]["kind"],self.rng):return
        if widget.id=="litter":self.start_routine(widget,"litter");return
        if widget.id in ("tree","tunnel","bed","soft_bed","hammock","rug","blanket","garden_patch"):self.start_furniture(widget);return
        target=self.laser_spots.get(widget.uid,widget);point=target.geometry().center()
        area=nearest_area(point.x(),point.y(),self.pet.areas());self.pet.perform_action("walk",15)
        self.interest=(widget.uid,now+15)
        self.pet.behaviour.target=clamp_position(point.x()-self.pet.width()/2,point.y()-self.pet.height()+20,self.pet.width(),self.pet.height(),area)
        self.speak(choose({"ball":"ball","mouse":"mouse","laser":"laser","wand":"wand","feather":"wand","catnip":"catnip"}.get(widget.id,"expectant")))
    def speak(self,text):self.pet.bubble.speak(text,self.pet.rect_global(),self.pet.areas())
    def repair(self):
        for w in self.widgets.values():
            if not w.down:w.repair()
    def obstacles(self):return [Rect(w.x(),w.y(),w.width(),w.height()) for w in self.widgets.values()]
    def shutdown(self):
        self.closing=True
        for spot in self.laser_spots.values():spot.close()
        for w in list(self.widgets.values()):
            w.record.update(x=w.x(),y=w.y());w.close()
        self.engine.save()

class ItemDragCard(QFrame):
    """Normal Qt mouse capture for owned-card drag; no Explorer file drag or global hook."""
    def __init__(self,id,pet,host,action_text=None,callback=None):
        super().__init__();self.id=id;self.pet=pet;self.host=host;self.start=None;self.ghost=None;self.cancelled=False
        self.setObjectName("itemCard");self.setFocusPolicy(Qt.FocusPolicy.StrongFocus);self.setMinimumWidth(145)
        self.card_row=QBoxLayout(QBoxLayout.Direction.TopToBottom,self);self.card_row.setContentsMargins(12,10,12,10);self.card_row.setSpacing(10)
        layout=self.card_row
        self.picture=QLabel();self.picture.setAlignment(Qt.AlignmentFlag.AlignCenter);self.picture.setPixmap(illustrated_item_pixmap(id,112));self.picture.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents);layout.addWidget(self.picture)
        info=QWidget();layout.addWidget(info);layout=QVBoxLayout(info);layout.setContentsMargins(0,0,0,0);layout.setSpacing(6)
        self.name=QLabel(BY_ID[id]["name"]);self.name.setObjectName("productName");self.name.setAlignment(Qt.AlignmentFlag.AlignCenter);self.name.setWordWrap(True);self.name.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents);layout.addWidget(self.name)
        self.detail=QLabel();self.detail.setObjectName("productDetail");self.detail.setAlignment(Qt.AlignmentFlag.AlignCenter);self.detail.setWordWrap(True);self.detail.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents);layout.addWidget(self.detail)
        if action_text:
            self.button=QPushButton(action_text);self.button.clicked.connect(lambda _checked=False:callback());layout.addWidget(self.button)
        self.setToolTip("按住图像拖到生活馆窗口外摆放；Esc 取消。"+BY_ID[id]["note"])
    def resizeEvent(self,event):
        self.card_row.setDirection(QBoxLayout.Direction.LeftToRight if self.width()>=280 else QBoxLayout.Direction.TopToBottom)
        super().resizeEvent(event)
    def minimumSizeHint(self):return QSize(145,self.card_row.minimumSize().height())
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
