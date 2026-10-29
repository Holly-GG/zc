from pathlib import Path
import json
from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QImage, QPixmap, QPainter, QRegion

def asset_path(name):
    path=Path(__file__).resolve().parent.parent/"assets"/name
    if path.suffix==".png" and not path.exists() and path.with_suffix(".webp").exists():return path.with_suffix(".webp")
    return path

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
        self.motion_specs={}
        manifest=asset_path("motion/atlases.json")
        if manifest.exists():
            try:self.motion_specs=json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError,ValueError):pass
        self.atlases={}
        for key,spec in self.motion_specs.items():self.extra[key]=(spec["file"],4)
        # Decode before first interactive frame: lazy alpha scans blocked mouse/probe processing.
        for key in self.extra:self.ensure(key)
        self.atlases.clear()
        self.head_pixels=json.loads(asset_path("motion/scale.json").read_text())["head_pixels"]
        self.stage_units=max(max(frame.width()/self.head_pixels[key][i] for i,frame in enumerate(frames)) for key,frames in self.frames.items())
        self.height_units=max(max(frame.height()/self.head_pixels[key][i] for i,frame in enumerate(frames)) for key,frames in self.frames.items())
    def stage_height(self,width):
        return round((width-16)*self.height_units/self.stage_units+20)
    def projection(self,state,index,width,height):
        source=self.frames[state][index]
        if state not in self.head_pixels:
            scale=min((width-16)/source.width(),(height-20)/source.height())
        else:scale=min((width-16)/self.stage_units,(height-20)/self.height_units)/self.head_pixels[state][index]
        w,h=source.width()*scale,source.height()*scale
        return QRectF((width-w)/2,height-h-10,w,h)


    def ensure(self,state):
        if state in self.frames:return state
        if state not in self.extra:return "idle"
        name,count=self.extra[state];atlas=self.atlases.get(name)
        if atlas is None:atlas=QImage(str(asset_path(name)));self.atlases[name]=atlas
        if atlas.isNull():return "idle"
        if state in self.motion_specs:
            spec=self.motion_specs[state];rects=spec["rects"]
            frames=[]
            for index,rect in enumerate(rects):
                source=atlas.copy(QRect(*rect));frame=QImage(source.size(),QImage.Format.Format_ARGB32);frame.fill(Qt.GlobalColor.transparent)
                painter=QPainter(frame)
                if "clips" in spec:
                    clip=QRegion()
                    for x,y,w in spec["clips"][index]:clip=clip.united(QRegion(QRect(x,y,w,1)))
                    painter.setClipRegion(clip)
                painter.drawImage(0,0,source);painter.end();frames.append(frame)
            w=max(f.width() for f in frames);h=max(f.height() for f in frames);aligned=[]
            for frame in frames:
                canvas=QImage(w,h,QImage.Format.Format_ARGB32);canvas.fill(Qt.GlobalColor.transparent)
                painter=QPainter(canvas);painter.drawImage((w-frame.width())//2,(h-frame.height())//2,frame);painter.end();aligned.append(canvas)
            frames=aligned
        else:
            if atlas.width()%count:return "idle"
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
        target=self.projection(state,frame_index,width,height)
        target.translate(0,bob)
        painter=QPainter(canvas);painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawImage(target,source)
        painter.end()
        # OS region follows the alpha bitmap, including paw gaps and concavities.
        mask=canvas.mask()
        self.cache[key]=(canvas,mask)
        if len(self.cache)>120:
            old=self.cache[key];self.cache.clear();self.cache[key]=old
        return self.cache[key]
