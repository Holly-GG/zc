"""Build a self-contained Windows exe and a directly downloadable ZIP."""
from pathlib import Path
import os,sys,subprocess,hashlib,shutil,zipfile,importlib.metadata

root=Path(__file__).resolve().parent.parent
os.chdir(root)
staging=root/"build"/"runtime-assets"
shutil.rmtree(staging,ignore_errors=True)
shutil.copytree(root/"assets",staging,ignore=shutil.ignore_patterns("*.blend","*.blend1","models","niangao-work.webp"))

shutil.copytree(root.parent/'fonts',staging/'fonts',dirs_exist_ok=True)

subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile','--windowed',
    '--name','Niangao-PhotoPet','--add-data',f'{staging}{os.pathsep}assets',
    '--exclude-module','PySide6.QtQml','--exclude-module','PySide6.QtQuick',
    '--exclude-module','PySide6.QtWebEngineCore','--exclude-module','PySide6.QtWebEngineWidgets',
    '--exclude-module','PySide6.Qt3DCore','--exclude-module','PySide6.Qt3DRender',
    '--exclude-module','PySide6.Qt3DExtras','--exclude-module','pytest','main.py'],check=True)
exe=root/'dist'/('Niangao-PhotoPet.exe' if sys.platform=='win32' else 'Niangao-PhotoPet')
assert exe.is_file()
print('EXE',exe,'bytes',exe.stat().st_size,flush=True)
