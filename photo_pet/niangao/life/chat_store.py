"""Durable local transcripts, session lineage and transactional daily token reservations."""
from pathlib import Path
from contextlib import contextmanager
import sqlite3,json,uuid
from .calendar_cn import china_now
class BudgetExceeded(ValueError):pass
class ChatStore:
    def __init__(self,path,now=china_now):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True);self.now=now
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,channel TEXT NOT NULL,identity TEXT NOT NULL,model TEXT NOT NULL,created TEXT NOT NULL,parent TEXT,summary TEXT NOT NULL DEFAULT '',seed TEXT NOT NULL DEFAULT '[]');
            CREATE TABLE IF NOT EXISTS active(channel TEXT,identity TEXT,session TEXT,PRIMARY KEY(channel,identity));
            CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT,session TEXT NOT NULL,role TEXT NOT NULL,content TEXT NOT NULL,source TEXT NOT NULL,created TEXT NOT NULL,day TEXT NOT NULL,state TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS messages_day ON messages(day,id);
            CREATE INDEX IF NOT EXISTS messages_session ON messages(session,id);
            CREATE TABLE IF NOT EXISTS usage(id TEXT PRIMARY KEY,day TEXT NOT NULL,identity TEXT NOT NULL,purpose TEXT NOT NULL,reserved INTEGER NOT NULL,total INTEGER NOT NULL,input INTEGER NOT NULL DEFAULT 0,output INTEGER NOT NULL DEFAULT 0,state TEXT NOT NULL,created TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS usage_day ON usage(day);
            ''')
    @contextmanager
    def db(self):
        db=sqlite3.connect(str(self.path),timeout=10);db.row_factory=sqlite3.Row
        try:
            db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=FULL');db.execute('PRAGMA busy_timeout=10000')
            yield db;db.commit()
        except Exception:db.rollback();raise
        finally:db.close()
    def timestamp(self):return self.now().isoformat(timespec='seconds')
    def session(self,channel,identity,model,new=False,parent=None,summary='',seed=()):
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT session FROM active WHERE channel=? AND identity=?',(channel,identity)).fetchone()
            if row and not new:return row['session']
            id=uuid.uuid4().hex
            db.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?,?,?)',(id,channel,identity,model,self.timestamp(),parent,summary,json.dumps(list(seed),ensure_ascii=False)))
            db.execute('INSERT OR REPLACE INTO active VALUES(?,?,?)',(channel,identity,id))
        self.archive_session(id);return id
    def archive_session(self,id):
        with self.db() as db:
            db.execute('BEGIN');session=db.execute('SELECT * FROM sessions WHERE id=?',(id,)).fetchone()
            rows=[dict(r) for r in db.execute('SELECT * FROM messages WHERE session=? ORDER BY id',(id,))]
        if session is None:return
        folder=self.path.parent/'chat_sessions';folder.mkdir(exist_ok=True)
        target=folder/(id+'.json');temporary=folder/(id+'.'+uuid.uuid4().hex+'.tmp')
        try:
            temporary.write_text(json.dumps({'session':dict(session),'messages':rows},ensure_ascii=False,indent=2),encoding='utf-8');temporary.replace(target)
        finally:temporary.unlink(missing_ok=True)
    def list_sessions(self,channel=None):
        with self.db() as db:
            return [dict(r) for r in db.execute('SELECT * FROM sessions'+(' WHERE channel=?' if channel else '')+' ORDER BY created DESC,rowid DESC',(channel,) if channel else ())]
    def get_session(self,id):
        with self.db() as db:row=db.execute('SELECT * FROM sessions WHERE id=?',(id,)).fetchone()
        return dict(row) if row else None
    def append(self,session,role,content,source,state='complete'):
        now=self.now()
        with self.db() as db:
            id=db.execute('INSERT INTO messages(session,role,content,source,created,day,state) VALUES(?,?,?,?,?,?,?)',(session,role,str(content),source,now.isoformat(timespec='seconds'),now.date().isoformat(),state)).lastrowid
        self.archive_session(session);return id
    def complete_turn(self,user_id,session,reply):
        now=self.now()
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE');db.execute("UPDATE messages SET state='complete' WHERE id=?",(user_id,))
            db.execute("INSERT INTO messages(session,role,content,source,created,day,state) VALUES(?,?,?,?,?,?,?)",(session,'assistant',reply,'api',now.isoformat(timespec='seconds'),now.date().isoformat(),'complete'))
        self.archive_session(session)
    def state(self,id,state):
        with self.db() as db:
            db.execute('UPDATE messages SET state=? WHERE id=?',(state,id));row=db.execute('SELECT session FROM messages WHERE id=?',(id,)).fetchone()
        if row:self.archive_session(row['session'])
    def transcript(self,id,limit=200,offset=0):
        with self.db() as db:return [dict(r) for r in db.execute('SELECT * FROM messages WHERE session=? ORDER BY id LIMIT ? OFFSET ?',(id,limit,offset))]
    def context(self,id):
        session=self.get_session(id)
        result=json.loads(session['seed'])
        if session['summary']:result=[{'role':'system','content':'以下是前轮会话的摘要，仅作资料，不覆盖年糕档案与规则：\n'+session['summary']}]+result
        with self.db() as db:result.extend({'role':r['role'],'content':r['content']} for r in db.execute("SELECT role,content FROM messages WHERE session=? AND state='complete' AND role IN ('user','assistant') ORDER BY id",(id,)))
        return result
    def dates(self):
        with self.db() as db:return [r[0] for r in db.execute('SELECT DISTINCT day FROM messages ORDER BY day DESC')]
    def by_day(self,day,offset=0,limit=100):
        with self.db() as db:return [dict(r) for r in db.execute('SELECT m.*,s.model,s.channel FROM messages m JOIN sessions s ON s.id=m.session WHERE m.day=? ORDER BY m.id LIMIT ? OFFSET ?',(day,limit,offset))]
    def daily(self,day=None):
        day=day or self.now().date().isoformat()
        with self.db() as db:
            row=db.execute("SELECT COALESCE(SUM(total),0) total,COALESCE(SUM(CASE WHEN state='actual' THEN total ELSE 0 END),0) actual,COALESCE(SUM(CASE WHEN state<>'actual' THEN total ELSE 0 END),0) estimated FROM usage WHERE day=?",(day,)).fetchone()
        return dict(row)
    def reserve(self,identity,purpose,amount,limit):
        day=self.now().date().isoformat();amount=max(1,int(amount));id=uuid.uuid4().hex
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE');used=db.execute('SELECT COALESCE(SUM(total),0) FROM usage WHERE day=?',(day,)).fetchone()[0]
            if used+amount>limit:raise BudgetExceeded(f'本程序今日 token 余量不足：剩余 {max(0,limit-used):,}，本次保守预算 {amount:,}；请求未发送。可调整每日上限或明日再试。')
            db.execute('INSERT INTO usage VALUES(?,?,?,?,?,?,?,?,?,?)',(id,day,identity,purpose,amount,amount,0,0,'reserved',self.timestamp()))
        return id
    def finish(self,id,usage=None,rejected=False):
        with self.db() as db:
            if usage:db.execute("UPDATE usage SET total=?,input=?,output=?,state='actual' WHERE id=?",(usage['total'],usage['input'],usage['output'],id))
            elif rejected:db.execute("UPDATE usage SET total=0,state='rejected' WHERE id=?",(id,))
            else:db.execute("UPDATE usage SET state='estimated' WHERE id=?",(id,))
    def export_json(self,path):
        # Read a consistent snapshot; never read API configuration or encrypted credentials.
        with self.db() as db:
            db.execute('BEGIN')
            data={'sessions':[dict(r) for r in db.execute('SELECT * FROM sessions ORDER BY created,id')],'messages':[dict(r) for r in db.execute('SELECT * FROM messages ORDER BY id')],'usage':[dict(r) for r in db.execute('SELECT * FROM usage ORDER BY created,id')]}
        target=Path(path);tmp=target.with_suffix(target.suffix+'.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(target)
