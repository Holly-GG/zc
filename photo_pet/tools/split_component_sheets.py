"""Mechanically split the requested generated sprite sheets into owned PNG layers.

The reviewed plan stores each sheet's actual row boundaries; generated sheets are
not assumed to obey an equal-row grid. Artwork is never resynthesized by this step.
"""
import argparse,json,hashlib
from pathlib import Path
from PySide6.QtGui import QImage

NAMES=('paper','frame','header','card','button','button-active','input','navigation',
       'corner-top','corner-bottom','character','objects')

def trim(image):
    rgba=image.convertToFormat(QImage.Format.Format_RGBA8888)
    data=bytes(rgba.constBits());w,h=rgba.width(),rgba.height();stride=rgba.bytesPerLine()
    rows=[0]*h;cols=[0]*w
    for y in range(h):
        for x,a in enumerate(data[y*stride+3:y*stride+w*4:4]):
            if a>=64:rows[y]+=1;cols[x]+=1
    ys=[y for y,v in enumerate(rows) if v>=max(3,w*.015)]
    xs=[x for x,v in enumerate(cols) if v>=max(3,h*.015)]
    if not xs or not ys:raise ValueError('Empty component')
    x=max(0,min(xs)-2);y=max(0,min(ys)-2)
    return image.copy(x,y,min(w,max(xs)+3)-x,min(h,max(ys)+3)-y)

def split(plan,root):
    records=[]
    for entry in plan:
        source=Path(entry['source']);sheet=QImage(str(source))
        if sheet.isNull():raise ValueError('Unreadable sheet: '+str(source))
        page=root/entry['page'];page.mkdir(parents=True,exist_ok=True)
        bands=entry['bands']
        for i,name in enumerate(entry.get('names',NAMES)):
            col=i%4;row=i//4
            box=entry.get('boxes',{}).get(name,[col/4,bands[row],1/4,bands[row+1]-bands[row]])
            x,y,w,h=[round(value*size) for value,size in zip(box,(sheet.width(),sheet.height(),sheet.width(),sheet.height()))]
            image=trim(sheet.copy(x,y,w,h))
            if name=='paper':
                # Plain paper is its center, separate from the perimeter frame.
                image=image.copy(image.width()//4,image.height()//4,image.width()//2,image.height()//2)
            target=page/(name+'.png');assert image.save(str(target),'PNG')
            records.append(dict(page=entry['page'],component=name,file=target.relative_to(root).as_posix(),
                width=image.width(),height=image.height(),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                source_sheet=source.name,source_rect=[x,y,w,h],origin='ai-reconstructed-from-reference',
                status='candidate-not-enabled' if name=='character' else 'ui-ornament'))
    (root/'manifest.json').write_text(json.dumps({'version':1,'components':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('plan',type=Path);p.add_argument('--output',type=Path,default=Path('assets/ui/layers/components'));a=p.parse_args()
    split(json.loads(a.plan.read_text()),a.output)
