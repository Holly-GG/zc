"""Run with a real graphical OpenGL desktop, never offscreen Qt platform."""
import sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFontDatabase,QFont
from niangao.pet import PetWindow
from niangao.config import Settings
from niangao.art import asset_path
parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path,default=Path("test-results/home3d"));args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
app=QApplication([]);app.setQuitOnLastWindowClosed(False)
font=QFontDatabase.addApplicationFont(str(asset_path("fonts/NiangaoSans.ttf")))
if font>=0:app.setFont(QFont(QFontDatabase.applicationFontFamilies(font)[0],10))
pet=PetWindow(Settings(args.output/"settings.json"));pet.show();pet.open_life();ui=pet.life_window
def start():
    ui.nav.setCurrentRow(2);ui.start_home()
    if not ui.home:print("HOME3D FAIL no OpenGL renderer",flush=True);pet.close();app.exit(1)
def finish():
    try:
        home=ui.home;assert home.model_mesh_count>=50 and home.view.isExposed()
        image=home.screen().grabWindow(home.view.winId()).toImage();assert not image.isNull()
        colors=set(image.pixel(x,y) for x in range(0,image.width(),3) for y in range(0,image.height(),3))
        assert len(colors)>30,"Renderer produced no detailed scene"
        image.save(str(args.output/"home3d.png"))
        ui.nav.setCurrentRow(0);app.processEvents();ui.grab().save(str(args.output/"overview.png"))
        print("HOME3D PASS: GLB 54 meshes, detailed native framebuffer, overview capture; model remains experimental",flush=True);pet.close()
    except Exception as exc:print("HOME3D FAIL",str(exc),flush=True);pet.close();app.exit(1)
QTimer.singleShot(1000,start);QTimer.singleShot(11000,finish);sys.exit(app.exec())
