from pathlib import Path
from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QImage, QPixmap, QPainter

def asset_path(name):return Path(__file__).resolve().parent.parent/"assets"/name

def alpha_bounds(image, threshold=30):
    rgba=image.convertToFormat(QImage.Format.Format_RGBA8888)
    data=bytes(rgba.constBits())
    stride=rgba.bytesPerLine()
    left,top,right,bottom=image.width(),image.height(),-1,-1
    for y in range(image.height()):
        for x in range(image.width()):
            if data[y*stride+x*4+3]>threshold:
                left=min(left,x);right=max(right,x);top=min(top,y);bottom=max(bottom,y)
    if right<left:raise ValueError("Cat asset has no visible alpha pixels")
    return QRect(max(0,left-2),max(0,top-2),min(image.width()-max(0,left-2),right-left+5),min(image.height()-max(0,top-2),bottom-top+5))

class CatArt:
    def __init__(self):
        self.frames={}
        for state,name,count in [("idle","niangao-idle.png",1),("walk","niangao-walk.png",4),("walk_left","niangao-walk-left.png",4),("sleep","niangao-sleep.png",1)]:
            atlas=QImage(str(asset_path(name)))
            if atlas.isNull():raise RuntimeError("Cannot load bundled image: "+name)
            if atlas.width()%count:raise ValueError("Atlas frame widths must be equal")
            frames=[]
            for index in range(count):
                frame=atlas.copy(QRect(index*(atlas.width()//count),0,atlas.width()//count,atlas.height()))
                frames.append(frame.copy(alpha_bounds(frame)))
            self.frames[state]=frames
        self.cache={}
        self.extra={key:("actions/"+key+".png",4) for key in ("groom","stretch","feed","pet","play_bow","yawn")}

    def ensure(self,state):
        if state in self.frames:return state
        if state not in self.extra:return "idle"
        name,count=self.extra[state];atlas=QImage(str(asset_path(name)))
        if atlas.isNull() or atlas.width()%count:return "idle"
        frames=[atlas.copy(QRect(i*(atlas.width()//count),0,atlas.width()//count,atlas.height())) for i in range(count)]
        try:
            bounds=alpha_bounds(frames[0])
            for frame in frames[1:]:bounds=bounds.united(alpha_bounds(frame))
            self.frames[state]=[frame.copy(bounds) for frame in frames]
        except ValueError:return "idle"
        return state

    def render(self,state,frame_index,width,height,bob=0):
        state=self.ensure(state)
        frame_index%=len(self.frames[state])
        key=(state,frame_index,width,height,bob)
        if key in self.cache:return self.cache[key]
        source=self.frames[state][frame_index]
        canvas=QPixmap(width,height);canvas.fill(Qt.GlobalColor.transparent)
        margin=8
        ratio=min((width-margin*2)/source.width(),(height-margin*2-abs(bob))/source.height())
        w,h=source.width()*ratio,source.height()*ratio
        painter=QPainter(canvas);painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawImage(QRectF((width-w)/2,height-h-margin+bob,w,h),source)
        painter.end()
        # OS region follows the alpha bitmap, including paw gaps and concavities.
        mask=canvas.mask()
        self.cache[key]=(canvas,mask)
        if len(self.cache)>120:
            old=self.cache[key];self.cache.clear();self.cache[key]=old
        return self.cache[key]
