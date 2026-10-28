import random, math, time
from .geometry import Rect, clamp_position, hits_edge

class Behaviour:
    def __init__(self, rng=None, clock=None):
        self.rng=rng or random.Random()
        self.clock=clock or time.monotonic
        self.state="idle"
        self.deadline=self.clock()+3
        self.target=None
        self.velocity=(0.0,0.0)
        self.edge_contact=False
        self.speed=58.0

    def action(self, name, seconds=4):
        self.state=name
        self.deadline=float("inf") if name=="sleep" else self.clock()+seconds
        self.velocity=(0,0)
        self.target=None

    def wake(self): self.action("idle",2)

    def tick(self, x,y,width,height,area,obstacles,dt,enabled=True):
        dt=max(0,min(dt,0.08)) # No teleport after a pause or suspend.
        now=self.clock()
        self.edge_contact=False
        if self.state=="sleep": return x,y
        if not enabled:
            if self.state!="idle" and now>=self.deadline:self.action("idle",2)
            return x,y
        if self.state!="walk":
            if now < self.deadline:return x,y
            self.state="walk"
            self.deadline=now+self.rng.uniform(6,14)
            self.target=clamp_position(self.rng.uniform(area.x,area.right),self.rng.uniform(area.y,area.bottom),width,height,area)
        if now>=self.deadline:
            self.action("idle",self.rng.uniform(2,5));return x,y
        if self.target is None:self.action("idle",1);return x,y
        dx,dy=self.target[0]-x,self.target[1]-y
        distance=math.hypot(dx,dy)
        if distance<4:self.action("idle",self.rng.uniform(2,4));return x,y
        step=min(distance,self.speed*dt)
        nx,ny=clamp_position(x+dx/distance*step,y+dy/distance*step,width,height,area)
        old=Rect(x,y,width,height)
        candidate=Rect(nx,ny,width,height)
        if hits_edge(old,candidate,obstacles):
            # Try tangent motion along a window edge, then pause/play at the edge.
            alternatives=[(nx,y),(x,ny)]
            for ax,ay in alternatives:
                if math.hypot(ax-x,ay-y)>0.05 and not hits_edge(old,Rect(ax,ay,width,height),obstacles):
                    self.edge_contact=True
                    self.velocity=(ax-x,ay-y)
                    return ax,ay
            self.edge_contact=True
            self.action("perch",self.rng.uniform(1,2.5))
            return x,y
        self.velocity=(nx-x,ny-y)
        return nx,ny
