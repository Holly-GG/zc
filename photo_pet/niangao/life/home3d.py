"""Real Qt3D room with Blender GLB; no claim of photoreal final cat or rig."""
from PySide6.QtCore import Qt,QUrl,QTimer,QEvent,QRect
from PySide6.QtGui import QColor,QVector3D,QQuaternion,QSurfaceFormat,QOpenGLContext
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QPushButton
from ..art import asset_path
from .layout import valid_placement,snapped
import math,uuid,os
os.environ.setdefault("QT3D_RENDERER","opengl")
class Home3D(QWidget):
    def __init__(self,engine,notify,parent=None):
        super().__init__(parent);self.engine=engine;self.notify=notify;self.placement=False;self.selected=None;self.drag=False;self.transforms={};self.keep=[]
        self.layout=QVBoxLayout(self);self.layout.setContentsMargins(0,0,0,0)
        fmt=QSurfaceFormat();fmt.setVersion(3,3);fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile);fmt.setDepthBufferSize(24)
        ctx=QOpenGLContext();ctx.setFormat(fmt)
        if not ctx.create() or ctx.format().majorVersion()<3:raise RuntimeError("实时3D需要 OpenGL 3.3；当前设备可使用静态渲染预览。")
        from PySide6.Qt3DCore import Qt3DCore as C
        from PySide6.Qt3DRender import Qt3DRender as R
        from PySide6.Qt3DExtras import Qt3DExtras as E
        self.C,self.R,self.E=C,R,E
        self.view=E.Qt3DWindow();self.view.setFormat(fmt);self.view.defaultFrameGraph().setClearColor(QColor("#EFF6F1"))
        self.root=C.QEntity();self.view.setRootEntity(self.root)
        self.container=QWidget.createWindowContainer(self.view);self.container.setMinimumSize(420,350);self.layout.addWidget(self.container)
        self.camera=self.view.camera();self.camera.lens().setPerspectiveProjection(38,1.4,.05,100);self.camera.setPosition(QVector3D(2.8,2.4,3.5));self.camera.setViewCenter(QVector3D(0,.5,0))
        self.orbit=E.QOrbitCameraController(self.root);self.orbit.setCamera(self.camera);self.orbit.setLinearSpeed(2);self.orbit.setLookSpeed(120)
        for pos in [(3,5,4),(-3,3,1)]:
            ent=C.QEntity(self.root);light=R.QPointLight(ent);light.setColor(QColor("#fff7e9"));light.setIntensity(.65)
            transform=C.QTransform(ent);transform.setTranslation(QVector3D(*pos));ent.addComponent(light);ent.addComponent(transform);self.keep.extend([ent,light,transform])
        self.room=C.QEntity(self.root);self.items=C.QEntity(self.root)
        self.cat=C.QEntity(self.root);self.cat_transform=C.QTransform(self.cat);self.cat.addComponent(self.cat_transform)
        from .glb import build_model
        self.model_mesh_count=build_model(asset_path("models/niangao-experimental.glb"),self.cat,C,R,E)
        self.view.installEventFilter(self)
        self.phase=0;self.timer=QTimer(self);self.timer.timeout.connect(self.animate);self.timer.start(50)
        self.rebuild()
    def box(self,parent,pos,size,color):
        ent=self.C.QEntity(parent);mesh=self.E.QCuboidMesh(ent);mesh.setXExtent(size[0]);mesh.setYExtent(size[1]);mesh.setZExtent(size[2])
        transform=self.C.QTransform(ent);transform.setTranslation(QVector3D(*pos))
        mat=self.E.QPhongMaterial(ent);mat.setDiffuse(QColor(color));mat.setAmbient(QColor.fromRgbF(QColor(color).redF()*.12,QColor(color).greenF()*.12,QColor(color).blueF()*.12));mat.setShininess(15)
        ent.addComponent(mesh);ent.addComponent(transform);ent.addComponent(mat);self.keep.extend([ent,mesh,transform,mat]);return ent
    def sphere(self,parent,pos,size,color):
        ent=self.C.QEntity(parent);mesh=self.E.QSphereMesh(ent);mesh.setRadius(1);mesh.setRings(16);mesh.setSlices(20)
        transform=self.C.QTransform(ent);transform.setTranslation(QVector3D(*pos));transform.setScale3D(QVector3D(*size))
        mat=self.E.QPhongMaterial(ent);mat.setDiffuse(QColor(color));mat.setAmbient(QColor.fromRgbF(QColor(color).redF()*.12,QColor(color).greenF()*.12,QColor(color).blueF()*.12))
        ent.addComponent(mesh);ent.addComponent(transform);ent.addComponent(mat);self.keep.extend([ent,mesh,transform,mat]);return ent
    def builtin_obstacles(self):
        scene=self.engine.data["scene"]
        if scene in ("desk","living","bedroom","kitchen"):
            return [{"id":"builtin","type":"builtin","x":-1.8 if scene!="kitchen" else 0,"z":-2.6,"scale":2.05 if scene=="kitchen" else 1,"rotation":0}]
        return []
    def rebuild(self):
        self.keep=self.keep[:6]
        self.room.setEnabled(False);self.room.deleteLater();self.items.setEnabled(False);self.items.deleteLater()
        self.room=self.C.QEntity(self.root);self.items=self.C.QEntity(self.root);self.transforms={}
        scene=self.engine.data["scene"]
        colors={"desk":"#d5ddd0","living":"#e7ddd0","bedroom":"#e5dedf","garden":"#89a97e","balcony":"#c4d9d1","kitchen":"#dfe9e5"}
        self.box(self.room,(0,-.06,0),(8,.1,8),colors[scene])
        if scene!="garden":
            self.box(self.room,(0,1.4,-4),(8,2.8,.08),"#f4f5ef")
            self.box(self.room,(-4,1.4,0),(.08,2.8,8),"#d6e2db")
            self.box(self.room,(1.4,1.5,-3.94),(2.3,1.4,.06),"#8CCCCA")
        if scene=="desk":
            self.box(self.room,(-1.8,.95,-2.6),(2.6,.12,1.2),"#a79078")
            for x in [-2.8,-.8]:
                for z in [-3,-2.2]:self.box(self.room,(x,.45,z),(.08,.9,.08),"#305E63")
            self.box(self.room,(-1.8,1.43,-2.8),(1.1,.8,.08),"#305E63")
            self.box(self.room,(-1.8,1.02,-2.4),(.9,.04,.3),"#8CCCCA")
        elif scene=="living":
            self.box(self.room,(-1.8,.35,-2.6),(2.8,.6,1.3),"#899F84");self.box(self.room,(-1.8,.8,-3.1),(2.8,.8,.25),"#8CCCCA")
        elif scene=="bedroom":
            self.box(self.room,(-1.8,.3,-2.6),(2.6,.5,1.8),"#899F84");self.box(self.room,(-1.8,.62,-2.6),(2.55,.2,1.75),"#EFF6F1")
        elif scene=="kitchen":
            self.box(self.room,(0,.55,-2.6),(6,1.1,.9),"#899F84");self.box(self.room,(0,1.14,-2.6),(6.1,.1,1),"#EFF6F1")
        elif scene=="balcony":
            for x in range(-7,8):self.box(self.room,(x/2,.6,-3.7),(.05,1.2,.06),"#305E63")
            self.box(self.room,(0,1.2,-3.7),(8,.06,.08),"#305E63")
        else:
            for i in range(18):
                a=i*2.399;r=3.6
                self.sphere(self.room,(math.cos(a)*r,.1,math.sin(a)*r),(.13,.13,.13),["#8CCCCA","#e8c9b1","#EFF6F1"][i%3])
        for item in self.engine.data["layouts"].get(scene,[]):self.add_entity(item)
    def add_entity(self,item):
        ent=self.C.QEntity(self.items);t=self.C.QTransform();t.setTranslation(QVector3D(item["x"],0,item["z"]));t.setRotationY(item.get("rotation",0));t.setScale(item.get("scale",1));ent.addComponent(t);self.transforms[item["id"]]=t;self.keep.extend([ent,t])
        kind=item["type"]
        if kind=="bed":
            self.box(ent,(0,.12,0),(1.2,.22,1),"#899F84");self.sphere(ent,(0,.24,0),(.5,.12,.4),"#EFF6F1")
        elif kind=="bowl":
            self.sphere(ent,(0,.08,0),(.25,.08,.25),"#40A387");self.sphere(ent,(0,.125,0),(.19,.02,.19),"#a79078")
        elif kind in ("scratcher","rug"):self.box(ent,(0,.035,0),(1.0 if kind=="scratcher" else 1.7,.06,.55 if kind=="scratcher" else 1.2),"#a79078" if kind=="scratcher" else "#8CCCCA")
        elif kind=="plant":
            self.box(ent,(0,.18,0),(.3,.35,.3),"#EFF6F1")
            for x in [-.12,0,.12]:self.sphere(ent,(x,.48,0),(.15,.22,.1),"#40A387")
        elif kind=="lamp":
            self.box(ent,(0,.3,0),(.05,.6,.05),"#305E63");self.sphere(ent,(0,.65,0),(.23,.14,.23),"#EFF6F1")
        elif kind in ("tree","hammock"):
            self.box(ent,(0,.5,0),(.14,1,.14),"#a79078");self.box(ent,(0,1,0),(1.05,.12,.7),"#899F84")
        elif kind=="litter":self.box(ent,(0,.15,0),(.9,.3,.7),"#8CCCCA")
    def focus_cat(self):self.camera.setPosition(QVector3D(1.2,1.1,2.2));self.camera.setViewCenter(QVector3D(0,.55,0))
    def animate(self):
        self.camera.lens().setAspectRatio(max(.1,self.view.width()/max(1,self.view.height())))
        self.phase+=.05;self.cat_transform.setScale(1+math.sin(self.phase*1.5)*.003)
    def move_item(self,item):
        others=self.engine.data["layouts"].get(self.engine.data["scene"],[])+self.builtin_obstacles()
        ok,reason=valid_placement(item,others)
        if not ok:return False,reason
        for i,old in enumerate(self.engine.data["layouts"][self.engine.data["scene"]]):
            if old["id"]==item["id"]:self.engine.data["layouts"][self.engine.data["scene"]][i]=item;break
        t=self.transforms.get(item["id"])
        if t:t.setTranslation(QVector3D(item["x"],0,item["z"]));t.setRotationY(item.get("rotation",0));t.setScale(item.get("scale",1))
        return True,""
    def eventFilter(self,obj,event):
        if obj==self.view and self.placement and self.selected:
            if event.type()==QEvent.Type.MouseButtonPress and event.button()==Qt.MouseButton.LeftButton:self.drag=True;return True
            if event.type()==QEvent.Type.MouseButtonRelease and self.drag:self.drag=False;self.engine.save();return True
            if event.type()==QEvent.Type.MouseMove and self.drag:
                p=event.position();viewport=QRect(0,0,self.view.width(),self.view.height())
                a=QVector3D(p.x(),self.view.height()-p.y(),0).unproject(self.camera.viewMatrix(),self.camera.projectionMatrix(),viewport)
                b=QVector3D(p.x(),self.view.height()-p.y(),1).unproject(self.camera.viewMatrix(),self.camera.projectionMatrix(),viewport)
                d=b-a
                if abs(d.y())>.00001:
                    hit=a+d*(-a.y()/d.y())
                    for item in self.engine.data["layouts"].get(self.engine.data["scene"],[]):
                        if item["id"]==self.selected:
                            candidate=dict(item,x=snapped(hit.x()),z=snapped(hit.z()));self.move_item(candidate);break
                return True
        return super().eventFilter(obj,event)
    def closeEvent(self,event):self.timer.stop();self.view.setRootEntity(None);super().closeEvent(event)
