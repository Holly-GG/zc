from PySide6.QtGui import QImage
def components(image):
    im=image.convertToFormat(QImage.Format.Format_RGBA8888);data=bytes(im.constBits());stride=im.bytesPerLine();width,height=im.width(),im.height();runs=[];parents=[];previous=[]
    def find(i):
        while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
        return i
    for y in range(height):
        current=[];x=0
        while x<width:
            while x<width and data[y*stride+x*4+3]<=128:x+=1
            left=x
            while x<width and data[y*stride+x*4+3]>128:x+=1
            if left==x:break
            index=len(runs);runs.append((left,y,x-left));parents.append(index);current.append(index)
            for old in previous:
                ox,oy,ow=runs[old]
                if ox>x:break
                if ox+ow>=left and ox<=x:
                    a,b=find(index),find(old)
                    if a!=b:parents[a]=b
        previous=current
    groups={}
    for i,r in enumerate(runs):groups.setdefault(find(i),[]).append(r)
    result=[]
    for segments in groups.values():
        area=sum(v[2] for v in segments)
        if area<2000:continue
        left=min(v[0] for v in segments);right=max(v[0]+v[2] for v in segments);top=min(v[1] for v in segments);bottom=max(v[1] for v in segments)+1
        result.append(dict(rect=[left,top,right-left,bottom-top],runs=segments,area=area))
    return result

def split_frames(image):
    from collections import defaultdict
    pieces=components(image)
    if len(pieces)!=16:raise ValueError("Expected sixteen separate opaque sprites, review atlas manually")
    ordered=sorted(pieces,key=lambda c:c["rect"][1])
    ordered=sum([sorted(ordered[i:i+4],key=lambda c:c["rect"][0]) for i in range(0,16,4)],[])
    all_rows=defaultdict(list)
    for index,piece in enumerate(ordered):
        for x,y,w in piece["runs"]:all_rows[y].append((x,x+w,index))
    result=[]
    for index,piece in enumerate(ordered):
        x,y,w,h=piece["rect"];left=max(0,x-3);top=max(0,y-3);right=min(image.width(),x+w+3);bottom=min(image.height(),y+h+3)
        expanded=defaultdict(list)
        for rx,ry,rw in piece["runs"]:
            for yy in range(max(top,ry-2),min(bottom,ry+3)):expanded[yy].append((max(left,rx-2),min(right,rx+rw+2)))
        clip=[]
        for yy,segments in expanded.items():
            merged=[]
            for a,b in sorted(segments):
                if merged and a<=merged[-1][1]:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
                else:merged.append((a,b))
            for ox,oz,owner in all_rows[yy]:
                if owner==index:continue
                next_segments=[]
                for a,b in merged:
                    if oz<=a or ox>=b:next_segments.append((a,b))
                    else:
                        if a<ox:next_segments.append((a,ox))
                        if oz<b:next_segments.append((oz,b))
                merged=next_segments
            clip.extend([a-left,yy-top,b-a] for a,b in merged if b>a)
        result.append({"rect":[left,top,right-left,bottom-top],"clip":clip,"opaque_area":piece["area"]})
    return result
