"""Time-based desktop physics, sub-stepped to avoid tunnelling through platforms."""
from dataclasses import dataclass
import math
@dataclass
class Body:
    x:float
    y:float
    vx:float=0.
    vy:float=0.
    grounded:bool=False
    def advance(self,dt,width,height,area,surfaces=(),bounce=False,running=False,settle_bounce=False):
        remaining=max(0,min(.25,dt));self.grounded=False
        while remaining>1e-9:
            step=min(1/120,remaining);remaining-=step
            self.vy+=850*step
            nx=self.x+self.vx*step;ny=self.y+self.vy*step
            if nx<area.x+12 or nx+width>area.right-12:
                self.vx=(-1 if nx+width>area.right-12 else 1)*abs(self.vx)
                nx=max(area.x+12,min(nx,area.right-width-12))
            floor=area.bottom-12
            for surface in surfaces:
                if nx+width-8>surface.x and nx+8<surface.right and self.y+height<=surface.y+1 and ny+height>=surface.y:
                    floor=min(floor,surface.y)
            if ny+height>=floor and self.vy>=0:
                ny=floor-height;self.grounded=True
                self.vy=-max(170,min(360,abs(self.vy)*.72)) if bounce else -abs(self.vy)*.24 if settle_bounce and self.vy>85 else 0
                if not running:self.vx*=math.exp(-7*step)
            self.x,self.y=nx,max(area.y+12,ny)
def accepts(stats,kind,rng):
    if kind=='consumable':probability=.92 if stats['satiety']<55 else .55 if stats['satiety']<88 else .12
    else:probability=(.2+.007*stats['mood'])*(.3+.007*stats['energy'])
    return rng.random()<min(.98,max(.03,probability))
