"""Capture actual layered pages and small windows in isolated temporary state."""
import argparse,sys,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication,QLabel
from niangao.typography import install_fonts
from niangao.config import Settings
from niangao.pet import PetWindow

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 app=QApplication([]);install_fonts(app);checks=[]
 with tempfile.TemporaryDirectory(prefix='niangao-review-') as state:
  pet=PetWindow(Settings(Path(state)/'settings.json'));pet.timer.stop();pet.open_life();ui=pet.life_window
  try:
   for width,height in ((740,540),(860,650)):
    ui.resize(width,height)
    for index in range(9):
     ui.nav.setCurrentRow(index)
     for _ in range(5):app.processEvents()
     scroll=ui.stack.widget(index);page=scroll.widget()
     assert page.width()<=scroll.viewport().width(),(index,width,page.width(),scroll.viewport().width())
     for label in page.findChildren(QLabel,'hero'):
      if label.isVisible():assert label.height()>=label.heightForWidth(label.width())
     assert ui.grab().save(str(a.output/f'{width}-{index}.png'))
     checks.append(dict(page=index,width=width,height=height,content_width=page.width(),viewport_width=scroll.viewport().width()))
   pet.open_focus();pet.open_work()
   for _ in range(5):app.processEvents()
   for name,widget in (('work',pet.work_panel),('focus',pet.focus_panel),('bubble',pet.bubble)):
    if name=='bubble':widget.text='今天也慢慢来，年糕陪着你。'
    assert widget.grab().save(str(a.output/(name+'.png')))
  finally:pet.close();app.processEvents()
 (a.output/'layout.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('COMPONENT_UI_REVIEW passed: 9 pages at 2 logical sizes; work/focus/bubble captured')
if __name__=='__main__':main()
