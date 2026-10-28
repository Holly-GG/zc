"""Blender 4.3+: experimental fur-groomed Niangao, NOT a photogrammetric scan."""
import bpy,math,random,json
from mathutils import Vector
from pathlib import Path
OUT=Path(__file__).resolve().parents[2]/"assets/models"
OUT.mkdir(parents=True,exist_ok=True)
random.seed(20210228)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def material(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    bsdf=m.node_tree.nodes.get("Principled BSDF");bsdf.inputs["Base Color"].default_value=(*color,1);bsdf.inputs["Roughness"].default_value=.72
    return m
brown=material("Seal brown fur",(.19,.115,.075));dark=material("Dark chocolate mask",(.07,.038,.026))
white=material("Warm white chest and paws",(.91,.88,.81));pink=material("Pink nose",(.66,.31,.35));blue=material("Blue iris",(.075,.29,.48))
black=material("Pupil",(.006,.008,.009));shine=material("Eye glint",(.95,.98,1))
furmats=[white,brown,dark,material("Cream tips",(.62,.51,.40))]
root=bpy.data.objects.new("Niangao_EXPERIMENTAL",None);bpy.context.collection.objects.link(root)
root["source"]="Reference-guided procedural prototype; not a scan or final likeness"
root["nose_mark"]="Small brown spot on viewer-right beside pink nose"
emitters=[]
def ellipsoid(name,pos,scale,mat,fur=0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,location=pos)
    o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat);o.parent=root
    for f in o.data.polygons:f.use_smooth=True
    if fur:emitters.append((Vector(pos),Vector(scale),mat,fur,name))
    return o
ellipsoid("Torso",(0,.04,.40),(.245,.39,.26),brown,2800)
ellipsoid("Rump",(0,.27,.37),(.25,.23,.26),brown,1400)
ellipsoid("Neck",(0,-.28,.49),(.19,.19,.25),white,1200)
ellipsoid("WhiteBib",(0,-.36,.37),(.19,.13,.25),white,1700)
ellipsoid("Head",(0,-.40,.70),(.235,.20,.215),dark,2300)
ellipsoid("Cheek.L",(-.13,-.45,.635),(.115,.12,.115),white,500)
ellipsoid("Cheek.R",(.13,-.45,.635),(.115,.12,.115),dark,500)
for x in [-.155,.155]:
    for y in [-.22,.27]:
        ellipsoid("Leg", (x,y,.20),(.065,.075,.18),brown,350)
        ellipsoid("WhiteSock",(x,y-.02,.105),(.071,.085,.10),white,220)
        ellipsoid("Paw",(x,y-.055,.045),(.082,.105,.045),white,160)
# Triangular ears with a rounded base, oriented anatomically on the head.
for side in [-1,1]:
    x=side*.16
    vertices=[(x-.075,-.40,.82),(x+.075,-.40,.82),(x+side*.035,-.35,1.035),(x,-.26,.84)]
    mesh=bpy.data.meshes.new("EarMesh");mesh.from_pydata(vertices,[],[(0,1,2),(1,3,2),(3,0,2),(0,3,1)]);mesh.update()
    o=bpy.data.objects.new("DarkEar",mesh);bpy.context.collection.objects.link(o);o.parent=root;o.data.materials.append(dark)
    bevel=o.modifiers.new("Soft ear edge","BEVEL");bevel.width=.016;bevel.segments=3
    o.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
# Asymmetric white blaze follows the head surface, with a small normal offset.
outline=[(-.02,.895),(.006,.88),(.008,.79),(.035,.745),(.021,.67),(-.065,.635),(-.075,.695),(-.035,.765)]
def face_y(x,z):
    q=max(.03,1-(x/.235)**2-((z-.70)/.215)**2)
    return -.40-.20*math.sqrt(q)-.004
v=[(x,face_y(x,z),z) for x,z in outline]
center=sum((Vector(t) for t in v),Vector())/len(v);v.append(tuple(center))
mesh=bpy.data.meshes.new("Asymmetric blaze");mesh.from_pydata(v,[],[(len(v)-1,i,(i+1)%(len(v)-1)) for i in range(len(v)-1)]);mesh.update()
o=bpy.data.objects.new("AsymmetricWhiteBlaze",mesh);bpy.context.collection.objects.link(o);o.parent=root;o.data.materials.append(white)
ellipsoid("Muzzle.L",(-.045,-.585,.635),(.075,.035,.05),white,0)
ellipsoid("Muzzle.R",(.043,-.585,.635),(.067,.033,.05),white,0)
for x in [-.086,.086]:
    ellipsoid("BlueEye",(x,-.583,.738),(.047,.018,.037),blue)
    ellipsoid("Pupil",(x,-.600,.738),(.016,.004,.029),black)
    ellipsoid("EyeHighlight",(x-.01,-.605,.750),(.006,.003,.006),shine)
# A genuine triangular pink nose and an independent, visible brown nose-side mark.
verts=[(-.028,-.632,.664),(.028,-.632,.664),(0,-.640,.632),(0,-.611,.651)]
mesh=bpy.data.meshes.new("Nose triangle");mesh.from_pydata(verts,[],[(0,1,2),(0,3,1),(1,3,2),(2,3,0)]);mesh.update()
o=bpy.data.objects.new("PinkNose",mesh);bpy.context.collection.objects.link(o);o.parent=root;o.data.materials.append(pink)
ellipsoid("SignatureBrownNoseSpot",(.030,-.638,.664),(.010,.004,.008),brown)
# Tail is a connected curved series; base is hidden naturally by the rump.
for i in range(11):
    t=i/10
    pos=(.11+.28*t,.37+.33*t,.34-.12*t+.06*math.sin(t*math.pi))
    ellipsoid("Tail",pos,(.095-.02*t,.11-.02*t,.095-.01*t),brown,250)
# Directional long-fur ribbons. Roots always grow outward before the comb tangent.
verts=[];faces=[];mids=[]
for center,scale,mat,count,name in emitters:
    for _ in range(count):
        n=Vector((random.gauss(0,1),random.gauss(0,1),random.gauss(0,1))).normalized()
        point=center+Vector((scale.x*n.x,scale.y*n.y,scale.z*n.z))
        normal=Vector((n.x/scale.x,n.y/scale.y,n.z/scale.z)).normalized()
        # Suppress internal roots where anatomical volumes overlap.
        inside=False
        for oc,os,om,_,on in emitters:
            if oc==center:continue
            d=point-oc
            if (d.x/os.x)**2+(d.y/os.y)**2+(d.z/os.z)**2<.87:inside=True;break
        if inside:continue
        if name=="Head" and point.y<-.53 and .60<point.z<.81 and abs(point.x)<.17:continue
        comb=Vector((point.x*.15,.18,-1))
        tangent=comb-normal*comb.dot(normal)
        if tangent.length<.001:tangent=normal.cross(Vector((1,0,0)))
        tangent.normalize()
        width_dir=normal.cross(tangent).normalized()
        length=random.uniform(.018,.040)*(1.6 if name in ["WhiteBib","Neck"] else 1)
        width=random.uniform(.00035,.0008);start=len(verts)
        for j in range(3):
            t=j/2;p=point+normal*(.002+length*.32*t)+tangent*(length*.78*t)
            half=width*(1-.88*t)
            verts.extend([tuple(p-width_dir*half),tuple(p+width_dir*half)])
        faces.extend([(start,start+1,start+3,start+2),(start+2,start+3,start+5,start+4)])
        idx=0 if mat==white else 2 if mat==dark else random.choice([1,1,1,3])
        mids.extend([idx,idx])
mesh=bpy.data.meshes.new("DirectionalLongFur");mesh.from_pydata(verts,[],faces);mesh.update()
o=bpy.data.objects.new("GroomedFur_Ribbons",mesh);bpy.context.collection.objects.link(o);o.parent=root
for m in furmats:mesh.materials.append(m)
for f,idx in zip(mesh.polygons,mids):f.material_index=idx;f.use_smooth=True
# Curved white whiskers, attached near the muzzle, never passing through eyes.
for side in [-1,1]:
    for i in range(5):
        cu=bpy.data.curves.new("Whisker","CURVE");cu.dimensions="3D";cu.bevel_depth=.00065;cu.bevel_resolution=1
        spline=cu.splines.new("POLY");spline.points.add(3)
        for j in range(4):
            t=j/3
            spline.points[j].co=(side*(.07+.23*t),-.605+.055*t,.63+(i-2)*.009+(i-2)*.012*t,1)
        ob=bpy.data.objects.new("WhiteWhisker",cu);bpy.context.collection.objects.link(ob);ob.parent=root;cu.materials.append(white)
# Export only the model; camera/lights/ground are preview-only.
bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
for obj in root.children:obj.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(OUT/"niangao-experimental.glb"),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_extras=True)
scene=bpy.context.scene
scene.render.engine="CYCLES";scene.cycles.samples=24;scene.cycles.use_denoising=False
scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.world.color=(.16,.19,.18)
def aim(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(1.45,-2.65,1.4));camera=bpy.context.object;camera.data.type="ORTHO";camera.data.ortho_scale=1.65;aim(camera,(0,0,.5));scene.camera=camera
for loc,power,size in [((1,-2,3),250,2.5),((-2,-1,1.8),180,2),((0,2,2.5),220,2)]:
    bpy.ops.object.light_add(type='AREA',location=loc);bpy.context.object.data.energy=power;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=size;aim(bpy.context.object,(0,0,.5))
scene.render.film_transparent=True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"niangao-model-source.blend"))
scene.render.filepath=str(OUT/"niangao-3d-preview.png");bpy.ops.render.render(write_still=True)
(OUT/"model-info.json").write_text(json.dumps({"status":"EXPERIMENTAL_NOT_FINAL_LIKENESS","fur_ribbon_count":len(faces)//2,
 "fur_vertices":len(verts),"animation":"idle rigid breathing only; no clothing or jumping","source":"Procedural Blender geometry informed by photographs, not a scan",
 "nose":"Pink triangle plus independent brown side spot","intersection_validation":"Static visual review only, not a guarantee for all poses"},indent=2))
print("MODEL_COMPLETE",OUT)
