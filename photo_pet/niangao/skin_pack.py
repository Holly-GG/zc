"""Local full-page artwork packs. Raster input only, no scripts or app data schema changes."""
import json, shutil, tempfile, uuid, zipfile
from functools import lru_cache
from pathlib import Path
from PySide6.QtGui import QImageReader

PAGES = ('settings','chat','home','care','status','diary','backpack','album')
ALIASES = {'settings':('r01-settings','r01','设置','性格与设置'),
 'chat':('r02-chat','r02','聊天','聊天陪伴'), 'home':('r03-home','r03','首页'),
 'care':('r04-care','r04','互动','互动陪伴'), 'status':('r05-status','r05','状态','宠物状态'),
 'diary':('r06-diary','r06','日记','魔法手账'), 'backpack':('r07-backpack','r07','背包','宠物背包'),
 'album':('r08-album','r08','相册','宠物相册')}
MAX_IMAGE = 40*1024*1024
MAX_PACK = 200*1024*1024

def image_size(path):
    reader=QImageReader(str(path));size=reader.size()
    if not reader.canRead() or size.width()<600 or size.height()<350 or size.width()*size.height()>40_000_000:
        raise ValueError('底图无法读取、尺寸过小或超过4000万像素：'+path.name)
    # Decode too: a valid header alone is insufficient. No transformed copy replaces the source.
    if reader.read().isNull():raise ValueError('底图内容损坏：'+path.name)
    return size.width(),size.height()

class SkinPack:
    def __init__(self,root):
        self.root=Path(root);manifest=self.root/'skin.json'
        if manifest.stat().st_size>64*1024:raise ValueError('皮肤配置过大')
        data=json.loads(manifest.read_text(encoding='utf-8'));self.pages={}
        if data.get('version')!=1:raise ValueError('不支持的皮肤版本')
        for page in PAGES:
            name=data.get('pages',{}).get(page)
            if not isinstance(name,str) or Path(name).name!=name or '/' in name or '\\' in name:
                raise ValueError('缺少或非法底图：'+page)
            path=self.root/name
            if path.suffix.lower() not in ('.png','.jpg','.jpeg','.webp') or path.is_symlink() or path.stat().st_size>MAX_IMAGE:
                raise ValueError('不支持的底图文件：'+page)
            image_size(path);self.pages[page]=path
    @classmethod
    @lru_cache(maxsize=1)
    def bundled(cls):
        from .art import asset_path
        return cls(asset_path('ui/fullpage'))
    @classmethod
    def active(cls,user_root):
        """Invalid/missing packs never make an existing dashboard unusable."""
        root=Path(user_root)/'page-skins';pointer=root/'active.json'
        try:
            if pointer.stat().st_size>2048:return None
            name=json.loads(pointer.read_text())['folder']
            if not isinstance(name,str) or not name.startswith('pack-') or Path(name).name!=name or '/' in name or '\\' in name:return None
            return cls(root/name)
        except (OSError,ValueError,KeyError,TypeError):return None

def import_skin_zip(source,user_root):
    """Atomically activate eight original images, preserving bytes and the previous pack."""
    root=Path(user_root)/'page-skins';root.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(source) as archive:
        infos=[v for v in archive.infolist() if not v.is_dir()]
        if len(infos)>128 or sum(v.file_size for v in infos)>MAX_PACK:raise ValueError('皮肤包超过200MB或128个文件')
        selected={}
        for info in infos:
            # We never extract archive paths. Only recognized images are copied to owned filenames.
            path=Path(info.filename.replace('\\','/'))
            if path.suffix.lower() not in ('.png','.jpg','.jpeg','.webp'):continue
            stem=path.stem.lower()
            supplied={'年糕猫猫陪伴聊天页-2':'chat','年糕的四季状态星盘-8':'status','年糕的星月陪伴-7':'care','年糕的月光花园-1':'home','年糕的海岸蓝相册-4':'album','年糕的蘑菇收藏柜-6':'backpack','年糕的魔法手账-3':'diary','年糕猫猫日记设置页-9':'settings'}
            stem=supplied.get(stem,stem)
            for page in PAGES:
                if stem==page or stem in ALIASES[page]:
                    if page in selected:raise ValueError('底图重复：'+page)
                    if info.file_size>MAX_IMAGE:raise ValueError('单张底图不能超过40MB')
                    selected[page]=info
        missing=[v for v in PAGES if v not in selected]
        if missing:raise ValueError('缺少底图：'+', '.join(missing)+'；请按R01-settings至R08-album命名')
        folder='pack-'+uuid.uuid4().hex
        with tempfile.TemporaryDirectory(prefix='staging-',dir=root) as temporary:
            staging=Path(temporary);pages={}
            for page,info in selected.items():
                name=page+Path(info.filename).suffix.lower();dest=staging/name
                with archive.open(info) as src,dest.open('wb') as dst:shutil.copyfileobj(src,dst,1024*1024)
                image_size(dest);pages[page]=name
            (staging/'skin.json').write_text(json.dumps({'version':1,'pages':pages},ensure_ascii=False,indent=2),encoding='utf-8')
            pack=SkinPack(staging)
            final=root/folder;staging.rename(final)
        pointer=root/'active.json';temp=root/('active-'+uuid.uuid4().hex+'.tmp')
        try:
            temp.write_text(json.dumps({'folder':folder}),encoding='utf-8');temp.replace(pointer)
        finally:temp.unlink(missing_ok=True)
        return SkinPack(final)
