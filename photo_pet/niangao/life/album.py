"""Local photo archive. Originals are copied, never moved or uploaded."""
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
import hashlib, shutil, sqlite3, struct, uuid
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImageReader
from .calendar_cn import CHINA, china_now

MAX_BYTES=64*1024*1024
MAX_PIXELS=40_000_000
CATEGORIES=('日常','午睡','玩耍','其他')

def _tiff_date(data):
    """Read bounded TIFF date tags from JPEG EXIF; ignore invalid/missing metadata."""
    if len(data)<8 or data[:2] not in (b'II',b'MM'):return None
    endian='<' if data[:2]==b'II' else '>'
    def u16(offset):return struct.unpack_from(endian+'H',data,offset)[0]
    def u32(offset):return struct.unpack_from(endian+'I',data,offset)[0]
    if u16(2)!=42:return None
    found={};visited=set()
    def walk(offset,depth=0):
        if depth>2 or offset in visited or offset<8 or offset+2>len(data):return
        visited.add(offset)
        for i in range(min(u16(offset),256)):
            entry=offset+2+i*12
            if entry+12>len(data):break
            tag,kind,count=u16(entry),u16(entry+2),u32(entry+4)
            if tag==0x8769 and kind==4 and count==1:walk(u32(entry+8),depth+1)
            if tag in (0x9003,0x9004,0x132) and kind==2 and 10<=count<=64:
                start=entry+8 if count<=4 else u32(entry+8)
                if start+count<=len(data):
                    text=data[start:start+count].split(b'\0')[0].decode('ascii',errors='ignore')
                    try:found[tag]=date.fromisoformat(text[:10].replace(':','-')).isoformat()
                    except ValueError:pass
    walk(u32(4))
    return next((found[tag] for tag in (0x9003,0x9004,0x132) if tag in found),None)

def photo_date(path):
    path=Path(path)
    try:
        with path.open('rb') as stream:
            if stream.read(2)==b'\xff\xd8':
                for _ in range(256):
                    marker=stream.read(2)
                    if len(marker)<2 or marker[0]!=255 or marker[1] in (0xDA,0xD9):break
                    if marker[1] in (0xD8,0x01) or 0xD0<=marker[1]<=0xD7:continue
                    length=struct.unpack('>H',stream.read(2))[0]-2
                    if length<0:break
                    payload=stream.read(length)
                    if marker[1]==0xE1 and payload.startswith(b'Exif\0\0'):
                        value=_tiff_date(payload[6:])
                        if value:return value,'拍摄日期（EXIF）'
    except (OSError,ValueError,struct.error):pass
    return datetime.fromtimestamp(path.stat().st_mtime,CHINA).date().isoformat(),'文件修改日期'

class AlbumStore:
    def __init__(self,root,now=china_now):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.now=now
        self.path=self.root/'album.sqlite3'
        with self.db() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS photos(
            id TEXT PRIMARY KEY,sha256 TEXT UNIQUE NOT NULL,original TEXT NOT NULL,
            thumbnail TEXT NOT NULL,day TEXT NOT NULL,date_source TEXT NOT NULL,
            title TEXT NOT NULL,category TEXT NOT NULL,note TEXT NOT NULL DEFAULT '',
            original_name TEXT NOT NULL,imported_at TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS photos_day ON photos(day,id);''')
    @contextmanager
    def db(self):
        db=sqlite3.connect(str(self.path),timeout=10);db.row_factory=sqlite3.Row
        try:yield db;db.commit()
        except Exception:db.rollback();raise
        finally:db.close()
    def owned(self,relative):
        path=(self.root/relative).resolve()
        if not path.is_relative_to(self.root.resolve()):raise ValueError('相册路径无效')
        return path
    def get(self,id):
        with self.db() as db:r=db.execute('SELECT * FROM photos WHERE id=?',(id,)).fetchone()
        return dict(r) if r else None
    def months(self):
        with self.db() as db:return [(r[0],r[1]) for r in db.execute('SELECT substr(day,1,7),count(*) FROM photos GROUP BY substr(day,1,7) ORDER BY 1 DESC')]
    def query(self,month='',category='',search='',offset=0,limit=12,ascending=False):
        where=[];params=[]
        if month:
            date.fromisoformat(month+'-01');where.append("substr(day,1,7)=?");params.append(month)
        if category:where.append('category=?');params.append(category)
        if search:where.append("instr(lower(title||' '||note),lower(?))>0");params.append(search[:200])
        sql=' FROM photos'+(' WHERE '+' AND '.join(where) if where else '')
        with self.db() as db:
            count=db.execute('SELECT count(*)'+sql,params).fetchone()[0]
            direction='ASC' if ascending else 'DESC'
            rows=db.execute('SELECT *'+sql+f' ORDER BY day {direction},imported_at {direction},id LIMIT ? OFFSET ?',params+[max(1,min(100,int(limit))),max(0,int(offset))])
            return [dict(r) for r in rows],count
    def import_one(self,source,override=None,cancel=None):
        source=Path(source)
        if not source.is_file() or source.stat().st_size>MAX_BYTES:raise ValueError('文件不存在或超过64MB')
        day,origin=(date.fromisoformat(override).isoformat(),'手动指定日期') if override else photo_date(source)
        id=uuid.uuid4().hex;temporary=self.root/(id+'.tmp');thumb=self.root/'thumbnails'/(id+'.webp')
        destination=None;committed=False
        try:
            digest=hashlib.sha256();size=0
            with source.open('rb') as src,temporary.open('wb') as out:
                while chunk:=src.read(1024*1024):
                    if cancel is not None and cancel.is_set():raise InterruptedError('导入已取消')
                    size+=len(chunk)
                    if size>MAX_BYTES:raise ValueError('文件超过64MB')
                    digest.update(chunk);out.write(chunk)
            sha=digest.hexdigest()
            with self.db() as db:old=db.execute('SELECT id FROM photos WHERE sha256=?',(sha,)).fetchone()
            if old:return old['id'],False
            reader=QImageReader(str(temporary));reader.setAutoTransform(True)
            dimensions=reader.size()
            if dimensions.width()<=0 or dimensions.height()<=0 or dimensions.width()*dimensions.height()>MAX_PIXELS:raise ValueError('图片无法读取或像素超过4000万')
            fmt=bytes(reader.format()).decode('ascii').lower()
            if fmt not in ('jpeg','jpg','png','webp','bmp','gif'):raise ValueError('支持 JPG、PNG、WebP、BMP、GIF（首帧）')
            if dimensions.width()>640 or dimensions.height()>480:reader.setScaledSize(dimensions.scaled(QSize(640,480),Qt.AspectRatioMode.KeepAspectRatio))
            try:image=reader.read()
            finally:del reader  # Release Qt's file handle before moving on Windows.
            if cancel is not None and cancel.is_set():raise InterruptedError('导入已取消')
            if image.isNull():raise ValueError('无法生成预览，图片可能损坏或超过解码内存限制')
            thumb.parent.mkdir(exist_ok=True)
            if not image.save(str(thumb),'WEBP',88):raise OSError('缩略图保存失败')
            ext={'jpeg':'jpg','jpg':'jpg'}.get(fmt,fmt)
            relative=f'{day}/{id}.{ext}';destination=self.owned(relative);destination.parent.mkdir(exist_ok=True)
            temporary.replace(destination)
            with self.db() as db:
                db.execute('INSERT INTO photos(id,sha256,original,thumbnail,day,date_source,title,category,original_name,imported_at) VALUES(?,?,?,?,?,?,?,?,?,?)',
                 (id,sha,relative,thumb.relative_to(self.root).as_posix(),day,origin,source.stem[:120],'日常',source.name[:250],self.now().isoformat(timespec='seconds')))
            committed=True;return id,True
        finally:
            temporary.unlink(missing_ok=True)
            if not committed:
                thumb.unlink(missing_ok=True)
                if destination:destination.unlink(missing_ok=True)
    def import_files(self,paths,override=None,cancel=None):
        paths=list(paths)
        if len(paths)>256:raise ValueError('每次最多导入256张照片，请分批选择')
        result={'imported':[],'duplicates':[],'errors':[],'cancelled':False}
        for source in paths:
            if cancel is not None and cancel.is_set():result['cancelled']=True;break
            try:
                id,created=self.import_one(source,override,cancel);result['imported' if created else 'duplicates'].append(id)
            except InterruptedError:result['cancelled']=True;break
            except (OSError,ValueError,sqlite3.Error) as exc:result['errors'].append({'name':Path(source).name,'error':str(exc)[:180]})
        return result
    def update(self,id,title,day,category,note=''):
        day=date.fromisoformat(day).isoformat()
        if category not in CATEGORIES:raise ValueError('分类无效')
        record=self.get(id)
        if not record:raise ValueError('照片已不在相册中')
        old=self.owned(record['original']);new=self.owned(f"{day}/{old.name}");moved=False
        try:
            if old!=new:
                new.parent.mkdir(exist_ok=True);old.replace(new);moved=True
            with self.db() as db:db.execute('UPDATE photos SET title=?,day=?,category=?,note=?,original=?,date_source=? WHERE id=?',
             (title.strip()[:120] or '未命名照片',day,category,note[:2000],new.relative_to(self.root).as_posix(),'手动指定日期' if day!=record['day'] else record['date_source'],id))
        except Exception:
            if moved:new.replace(old)
            raise
    def remove(self,id):
        record=self.get(id)
        if not record:return
        with self.db() as db:db.execute('DELETE FROM photos WHERE id=?',(id,))
        # Only managed copies, never the user's source file. Locked files remain as
        # unreferenced local copies rather than causing a failed/partial source deletion.
        retained=[]
        for key in ('original','thumbnail'):
            try:self.owned(record[key]).unlink(missing_ok=True)
            except OSError:retained.append(record[key])
        return retained
    def export_original(self,id,destination):
        record=self.get(id)
        if not record:raise ValueError('照片不存在')
        source=self.owned(record['original']);target=Path(destination)
        if source.resolve()==target.resolve():return
        shutil.copy2(source,target)
