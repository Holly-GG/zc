from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float
    @property
    def right(self): return self.x + self.w
    @property
    def bottom(self): return self.y + self.h
    def intersects(self, other):
        return self.x < other.right and self.right > other.x and self.y < other.bottom and self.bottom > other.y
    def overlap(self, other):
        return max(0, min(self.right, other.right)-max(self.x, other.x))*max(0, min(self.bottom, other.bottom)-max(self.y, other.y))
    def contains(self, other):
        return self.x <= other.x and self.y <= other.y and self.right >= other.right and self.bottom >= other.bottom

def clamp_position(x, y, width, height, area, margin=12):
    mx = min(margin, max(0, (area.w-width)/2))
    my = min(margin, max(0, (area.h-height)/2))
    return (max(area.x+mx, min(x, area.right-width-mx)),
            max(area.y+my, min(y, area.bottom-height-my)))

def nearest_area(x, y, areas):
    return min(areas, key=lambda a:(max(a.x-x,0,x-a.right))**2+(max(a.y-y,0,y-a.bottom))**2)

def edge_barriers(window, thickness=3):
    return [Rect(window.x,window.y,window.w,thickness),
            Rect(window.x,window.bottom-thickness,window.w,thickness),
            Rect(window.x,window.y,thickness,window.h),
            Rect(window.right-thickness,window.y,thickness,window.h)]

def hits_edge(before, after, windows):
    # Window EDGES are obstacles; a maximized app does not ban the whole desktop.
    # Allow escape from an edge moved onto the pet by another application.
    for window in windows:
        for edge in edge_barriers(window):
            old, new = before.overlap(edge), after.overlap(edge)
            if new > 0 and (old == 0 or new > old + 0.01):
                return True
    return False

def bubble_position(pet, width, height, area, gap=14):
    candidates=[(pet.x+(pet.w-width)/2,pet.y-height-gap),
                (pet.right+gap,pet.y+(pet.h-height)/2),
                (pet.x-width-gap,pet.y+(pet.h-height)/2),
                (pet.x+(pet.w-width)/2,pet.bottom+gap)]
    for x,y in candidates:
        x,y=clamp_position(x,y,width,height,area,4)
        box=Rect(x,y,width,height)
        if area.contains(box) and not pet.intersects(box): return x,y
    return None

def physical_to_logical(rect, native_origin, logical_origin, scale):
    scale=max(0.5,scale)
    return Rect(logical_origin[0]+(rect.x-native_origin[0])/scale,
                logical_origin[1]+(rect.y-native_origin[1])/scale,
                rect.w/scale,rect.h/scale)
