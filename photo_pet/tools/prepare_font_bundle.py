"""Build-time only. python photo_pet/tools/prepare_font_bundle.py CACHE_DIRECTORY."""
import hashlib,json,shutil,sys,zipfile
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools import subset

repository=Path(__file__).resolve().parents[2];project=repository/'photo_pet';cache=Path(sys.argv[1]);out=repository/'fonts';out.mkdir(exist_ok=True)
text=''.join(path.read_text(encoding='utf-8') for path in (project/'niangao').rglob('*.py'))
chars=set(text)|{chr(i) for i in range(32,256)}
for a in range(0xb0,0xd8):
    for b in range(0xa1,0xff):
        try:chars.add(bytes([a,b]).decode('gb2312'))
        except UnicodeDecodeError:pass
specs=[('NotoSansSC.ttf','NiangaoSans.ttf','Niangao UI Sans',400),('NotoSerifSC.ttf','NiangaoSerif.ttf','Niangao Journal Serif',600),('Allura-Regular.ttf','NiangaoScript.ttf','Niangao Journal Script',400)]
manifest=[]
for source,target,family,weight in specs:
    font=TTFont(cache/source)
    if 'fvar' in font:font=instantiateVariableFont(font,{'wght':weight},inplace=True)
    sub=subset.Subsetter();sub.populate(text=''.join(chars));sub.subset(font)
    for record in font['name'].names:
        if record.nameID in (1,2,3,4,6,16,17):
            value='Regular' if record.nameID in (2,17) else family.replace(' ','')+'-Regular' if record.nameID in (3,6) else family
            record.string=value.encode(record.getEncoding(),errors='replace')
    font.save(out/target)
    manifest.append({'file':target,'family':family,'weight':weight,'source':source,'sha256':hashlib.sha256((out/target).read_bytes()).hexdigest()})
    print(target,(out/target).stat().st_size)
for source,target in [(project/'licenses/NOTO-OFL.txt','NotoSansSC-OFL.txt'),(cache/'NotoSerifSC-OFL.txt','NotoSerifSC-OFL.txt'),(cache/'Allura-OFL.txt','Allura-OFL.txt')]:shutil.copyfile(source,out/target)
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
with zipfile.ZipFile(repository/'Niangao-Fonts.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for path in sorted(out.iterdir()):
        if path.is_file():archive.write(path,'fonts/'+path.name)
