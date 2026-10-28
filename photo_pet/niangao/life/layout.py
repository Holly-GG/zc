from math import cos,sin,radians
SIZES={"builtin":(3.0,1.6),"bed":(1.2,1.0),"bowl":(.55,.55),"scratcher":(1.0,.55),"rug":(1.7,1.2),"plant":(.55,.55),"lamp":(.5,.5),"tree":(1.0,1.0),"hammock":(1.2,.7),"litter":(.9,.7)}
def bounds(item):
    w,d=SIZES[item["type"]];s=item.get("scale",1);a=radians(item.get("rotation",0))
    return abs(w*s*cos(a))+abs(d*s*sin(a)),abs(w*s*sin(a))+abs(d*s*cos(a))
def valid_placement(item,others,limit=3.8):
    w,d=bounds(item);x,z=item["x"],item["z"]
    if abs(x)+w/2>limit or abs(z)+d/2>limit:return False,"超出房间范围"
    if abs(x)<w/2+.7 and abs(z)<d/2+.7:return False,"请保留中央年糕活动区"
    for other in others:
        if other.get("id")==item.get("id"):continue
        ow,od=bounds(other)
        if abs(x-other["x"])<(w+ow)/2+.06 and abs(z-other["z"])<(d+od)/2+.06:return False,"家具占地重叠"
    return True,""
def snapped(value,enabled=True):return round(value*4)/4 if enabled else value
