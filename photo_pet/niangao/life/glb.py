"""Read our unskinned, embedded-buffer glTF 2.0 model without Qt importer plugins."""
import json,struct
from PySide6.QtCore import QByteArray
from PySide6.QtGui import QMatrix4x4,QColor,QVector3D,QQuaternion
def read_glb(path):
    raw=path.read_bytes()
    if len(raw)<20 or struct.unpack_from("<III",raw)!=(0x46546c67,2,len(raw)):raise ValueError("Invalid GLB 2.0")
    offset=12;doc=None;binary=None
    while offset+8<=len(raw):
        size,kind=struct.unpack_from("<II",raw,offset);offset+=8
        chunk=raw[offset:offset+size];offset+=size
        if kind==0x4e4f534a:doc=json.loads(chunk)
        elif kind==0x004e4942:binary=chunk
    if doc is None or binary is None:raise ValueError("Missing GLB chunks")
    return doc,binary
def build_model(path,parent,C,R,E):
    doc,binary=read_glb(path)
    keep=[];parent._model_keep=keep
    def attribute(index,geometry,name=None):
        a=doc["accessors"][index];view=doc["bufferViews"][a["bufferView"]]
        if view.get("buffer",0)!=0 or "sparse" in a:raise ValueError("Only internal dense accessors supported")
        sizes={5126:4,5125:4,5123:2,5121:1}
        components={"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4}[a["type"]];size=sizes[a["componentType"]]
        start=view.get("byteOffset",0);end=start+view["byteLength"]
        if end>len(binary):raise ValueError("Buffer exceeds GLB payload")
        buffer=C.QBuffer(geometry);buffer.setData(QByteArray(binary[start:end]))
        attr=C.QAttribute(geometry);attr.setBuffer(buffer);attr.setCount(a["count"]);attr.setVertexSize(components)
        attr.setByteOffset(a.get("byteOffset",0));attr.setByteStride(view.get("byteStride",size*components))
        base={5126:C.QAttribute.VertexBaseType.Float,5125:C.QAttribute.VertexBaseType.UnsignedInt,5123:C.QAttribute.VertexBaseType.UnsignedShort,5121:C.QAttribute.VertexBaseType.UnsignedByte}
        attr.setVertexBaseType(base[a["componentType"]])
        if name:attr.setName(name);attr.setAttributeType(C.QAttribute.AttributeType.VertexAttribute)
        else:attr.setAttributeType(C.QAttribute.AttributeType.IndexAttribute)
        geometry.addAttribute(attr);keep.extend([buffer,attr]);return attr
    def node(index,parent):
        data=doc["nodes"][index];ent=C.QEntity(parent);ent.setObjectName(data.get("name","model"))
        transform=C.QTransform(ent)
        if "matrix" in data:
            mat=QMatrix4x4(*data["matrix"]);mat=mat.transposed();transform.setMatrix(mat)
        else:
            transform.setTranslation(QVector3D(*data.get("translation",[0,0,0])))
            r=data.get("rotation",[0,0,0,1]);transform.setRotation(QQuaternion(r[3],r[0],r[1],r[2]))
            transform.setScale3D(QVector3D(*data.get("scale",[1,1,1])))
        ent.addComponent(transform);keep.extend([ent,transform])
        if "mesh" in data:
            for primitive in doc["meshes"][data["mesh"]]["primitives"]:
                if primitive.get("mode",4)!=4:continue
                part=C.QEntity(ent);geo=C.QGeometry(part)
                pos=attribute(primitive["attributes"]["POSITION"],geo,C.QAttribute.defaultPositionAttributeName())
                if "NORMAL" in primitive["attributes"]:attribute(primitive["attributes"]["NORMAL"],geo,C.QAttribute.defaultNormalAttributeName())
                count=attribute(primitive["indices"],geo).count() if "indices" in primitive else pos.count()
                renderer=R.QGeometryRenderer(part);renderer.setGeometry(geo);renderer.setVertexCount(count);renderer.setPrimitiveType(R.QGeometryRenderer.PrimitiveType.Triangles)
                material=E.QPhongMaterial(part)
                m=doc.get("materials",[])[primitive.get("material",0)] if doc.get("materials") else {}
                color=m.get("pbrMetallicRoughness",{}).get("baseColorFactor",[.8,.8,.8,1])
                q=QColor.fromRgbF(*color);material.setDiffuse(q);material.setAmbient(QColor.fromRgbF(color[0]*.3,color[1]*.3,color[2]*.3));material.setShininess(8)
                part.addComponent(renderer);part.addComponent(material);keep.extend([part,geo,renderer,material])
        for child in data.get("children",[]):node(child,ent)
    for index in doc["scenes"][doc.get("scene",0)]["nodes"]:node(index,parent)
    return len(doc.get("meshes",[]))
