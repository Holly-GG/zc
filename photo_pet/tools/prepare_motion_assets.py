"""Encode generated atlases losslessly; annotate reviewed frame rectangles, no pose fabrication."""
import json,hashlib,sys
from pathlib import Path
from PySide6.QtGui import QImage
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from niangao.interaction.actions import ROWS
from component_frames import split_frames
ROOT=Path(__file__).resolve().parents[1]
# Source generation files remain untouched; each row is reviewed separately.
SOURCES={
 "a":"exec-d30cb578-a29a-4228-989c-76c350ba7c6d.png",
 "b":"exec-2bbbbe27-4142-4d83-a5b2-590d6daf78c6.png",
 "c":"exec-2cfbbe72-e9cd-44fa-a60d-555a5e4b68d4.png",
 "d":"exec-cc164663-c666-4359-bcc7-745c6f2bf910.png",
 "e":"exec-732a8252-42be-437f-89e3-ed2a88b451ca.png",
 "f":"exec-cc3ba358-36f2-43be-84a0-bbc807b4ae2a.png",
 "g":"exec-9ea2985b-3725-445c-a3e0-58bc83aaebd8.png","h":"exec-3aa8ca21-d128-46d0-8a77-19cfe2ed67bb.png"}
def prepare(source_dir):
    destination=ROOT/"assets/motion";destination.mkdir(parents=True,exist_ok=True)
    specs={};provenance={}
    for key,filename in SOURCES.items():
        path=Path(source_dir)/filename
        if not path.exists():continue
        image=QImage(str(path))
        if image.size().width()!=1254 or image.size().height()!=1254:raise ValueError("Review coordinates for different generation dimensions")
        target=destination/(key+".webp")
        assert image.save(str(target),"WEBP",100)
        decoded=QImage(str(target)).convertToFormat(QImage.Format.Format_RGBA8888);original=image.convertToFormat(QImage.Format.Format_RGBA8888)
        # Lossless encoding preserves all visible RGBA pixels (transparent RGB is immaterial).
        a,b=bytes(original.constBits()),bytes(decoded.constBits())
        assert len(a)==len(b)
        assert all(a[i+3]==b[i+3] and (a[i+3]==0 or a[i:i+3]==b[i:i+3]) for i in range(0,len(a),4))
        frames=split_frames(image)
        for row,action in enumerate(ROWS[key]):
            selected=frames[row*4:row*4+4]
            specs[action]={"file":"motion/"+key+".webp","rects":[f["rect"] for f in selected],
               "clips":[f["clip"] for f in selected],"opaque_areas":[f["opaque_area"] for f in selected],"fps":2.8,
               "origin":"AI photographic pose completion; component-isolated atlas frames"}
        provenance[key]={"source":filename,"source_sha256":hashlib.file_digest(path.open("rb"),"sha256").hexdigest(),"webp_sha256":hashlib.file_digest(target.open("rb"),"sha256").hexdigest(),"lossless_visible_pixels":True}
    (destination/"atlases.json").write_text(json.dumps(specs,ensure_ascii=False,indent=2),encoding="utf-8")
    (destination/"provenance.json").write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Prepared",len(specs),"actions",sum(p.stat().st_size for p in destination.glob("*.webp")),"bytes")
if __name__=="__main__":prepare(sys.argv[1] if len(sys.argv)>1 else "/workspace/generated_images")
