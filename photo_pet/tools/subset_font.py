"""Build-time only: create an OFL UI font subset from Noto Sans SC variable font."""
import sys
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools import subset
root=Path(__file__).resolve().parents[1]
text="".join(p.read_text(encoding="utf-8") for p in (root/"niangao").rglob("*.py"))
chars=set(text)|set(chr(i) for i in range(32,256))
for a in range(0xb0,0xd8):
    for b in range(0xa1,0xff):
        try:chars.add(bytes([a,b]).decode("gb2312"))
        except UnicodeDecodeError:pass
font=instantiateVariableFont(TTFont(sys.argv[1]),{"wght":400},inplace=True)
options=subset.Options();sub=subset.Subsetter(options=options);sub.populate(text="".join(chars));sub.subset(font)
for record in font["name"].names:
    if record.nameID in (1,3,4,6,16,17):
        value="NiangaoUISans-Regular" if record.nameID in (3,6) else "Regular" if record.nameID==17 else "Niangao UI Sans"
        record.string=value.encode(record.getEncoding(),errors="replace")
out=root/"assets/fonts/NiangaoSans.ttf";out.parent.mkdir(parents=True,exist_ok=True);font.save(out);print(out,out.stat().st_size)
