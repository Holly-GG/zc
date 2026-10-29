"""Staged local desktop interactions. Food is charged only at the completed bite."""
import math,time
from .geometry import nearest_area,clamp_position
from .dialogue import choose
PACKETS={'freeze_dried':('freeze_piece',8),'food':('kibble_piece',12),'kitten_food':('kibble_piece',12),'senior_food':('kibble_piece',12)}
SMALL_FOOD={'freeze_piece','kibble_piece'}
MEAL_BOWLS={'food_bowl','bowl'}
class DesktopRoutine:
    def __init__(self,pet,widget,kind,clock=time.monotonic):
        self.pet=pet;self.widget=widget;self.uid=widget.uid;self.kind=kind;self.clock=clock;self.started=clock();self.phase='approach';self.index=-1;self.committed=False;self.cancelled=False
        self.origin=(pet.x(),pet.y());self.reference=(widget.x(),widget.y())
        self.approach=max(1.5,min(6,math.hypot(pet.x()-widget.x(),pet.y()-widget.y())/170))
        self.steps=[('闻一闻','expectant',1),('慢慢吃','feed',3),('舔舔嘴','mouth_lick',1.5)] if kind=='food' else [('闻闻猫砂','expectant',1),('前爪刨砂','scratch',2),('安静如厕','expectant',4),('盖好猫砂','scratch',2),('整理爪爪','lick_paw',1.5)]
        self.total=self.approach+sum(v[2] for v in self.steps);pet.director.cancel();pet.cursor_target=None;pet.cursor_mode=False;pet.perform_action('walk',self.approach+1,False)
    @property
    def progress(self):return min(1,max(0,(self.clock()-self.started)/self.total))
    def cancel(self):
        self.cancelled=True
        if self.pet.furniture is self:self.pet.furniture=None
        self.pet.behaviour.action('idle',3)
    def commit(self):
        if self.committed:return True
        m=self.pet.desktop;w=m.widgets.get(self.uid)
        if w is None:return False
        if self.kind=='litter':
            w.record['dirt']=min(3,w.record.get('dirt',0)+1);w.rebuild_mask();m.engine.event('litter_use','年糕使用猫砂盆，留下待清理的砂团');m.engine.data['stats']['cleanliness']=max(0,m.engine.data['stats']['cleanliness']-1);ok=True;text='盖好猫砂啦，记得帮我铲一铲。'
        elif w.id in MEAL_BOWLS:
            ok,text=m.engine.care('meal')
            if ok:w.record['servings']=max(0,w.record.get('servings',3)-1);w.rebuild_mask()
        else:
            ok,text=m.engine.use(w.id)
            if ok:m.remove(self.uid)
        if ok:self.committed=True;m.save();m.speak(text)
        return ok
    def tick(self,now):
        if self.cancelled:return
        p=self.pet;m=p.desktop;w=m.widgets.get(self.uid)
        if p.dragging or p.pressed or p.work_mode or (not self.committed and (w is None or w.down or abs(w.x()-self.reference[0])+abs(w.y()-self.reference[1])>25)):
            self.cancel();return
        elapsed=now-self.started
        if elapsed<self.approach:
            self.phase='靠近食物' if self.kind=='food' else '走向猫砂盆'
            x,y=self.reference;rx=x+self.widget.width()/2;ry=y+self.widget.width()*.76
            area=nearest_area(rx,ry,p.areas());tx,ty=clamp_position(rx-p.width()/2,ry-p.height()+10,p.width(),p.height(),area)
            t=elapsed/self.approach;t=t*t*(3-2*t);x=self.origin[0]+(tx-self.origin[0])*t;y=self.origin[1]+(ty-self.origin[1])*t
            p.float_pos=(x,y);p.move(round(x),round(y));return
        t=elapsed-self.approach;acc=0
        for index,(label,action,seconds) in enumerate(self.steps):
            if t<acc+seconds:
                if index!=self.index:
                    # Charge only after eating, or after covering litter; interruption before this is free.
                    if index==len(self.steps)-1 and not self.commit():self.cancel();return
                    self.index=index;self.phase=label;p.perform_action(action,seconds+1,False)
                return
            acc+=seconds
        # A suspended app can skip animation phases, but commit still executes at most once.
        if not self.committed:self.commit()
        self.cancel()
