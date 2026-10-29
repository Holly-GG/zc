"""Bundled, licensed typography. A sidecar fonts/ folder can override the bundle."""
import json,re,sys
from pathlib import Path
from PySide6.QtGui import QFont,QFontDatabase
from .art import asset_path

DEFAULT={'body':{'family':'Niangao UI Sans','file':'NiangaoSans.ttf','size':13},
 'title':{'family':'Niangao Journal Serif','file':'NiangaoSerif.ttf','size':24},
 'script':{'family':'Niangao Journal Script','file':'NiangaoScript.ttf','size':24}}

def font_directory():
    external=Path(sys.executable).parent/'fonts' if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[2]/'fonts'
    return external if (external/'roles.json').exists() else asset_path('fonts')

def roles():
    result={key:dict(value) for key,value in DEFAULT.items()}
    try:
        data=json.loads((font_directory()/'roles.json').read_text(encoding='utf-8'))
        for role,entry in result.items():
            value=data.get(role,{})
            if not isinstance(value,dict):continue
            family=value.get('family','');file=value.get('file','');size=value.get('size')
            if isinstance(family,str) and re.fullmatch(r'[A-Za-z0-9 _-]{1,64}',family):entry['family']=family
            if isinstance(file,str) and Path(file).name==file and file.lower().endswith(('.ttf','.otf')):entry['file']=file
            low,high=(12,17) if role=='body' else (20,30)
            if isinstance(size,int) and not isinstance(size,bool) and low<=size<=high:entry['size']=size
    except (OSError,ValueError):pass
    return result

def install_fonts(app):
    configured=roles();loaded={}
    for role,entry in configured.items():
        path=font_directory()/entry['file']
        if path.exists() and path.resolve().is_relative_to(font_directory().resolve()):
            id=QFontDatabase.addApplicationFont(str(path))
            if id>=0:loaded[role]=QFontDatabase.applicationFontFamilies(id)[0]
    body=QFont(loaded.get('body','Microsoft YaHei'));body.setPixelSize(configured['body']['size']);app.setFont(body)
    return loaded

def stylesheet_tokens():
    data=roles()
    return {key:value for role,entry in data.items() for key,value in ((role+'_font',entry['family']),(role+'_size',str(entry['size'])))}
