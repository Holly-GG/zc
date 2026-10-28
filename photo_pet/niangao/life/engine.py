from datetime import datetime,date
from pathlib import Path
import json,os,time,uuid,math,random,tempfile
from .age import age_info
from .catalog import BY_ID,SCENES
STAT_NAMES={"satiety":"饱食度","cleanliness":"清洁度","energy":"精力","mood":"心情","health":"健康（虚拟）"}
CARE={"meal":({"satiety":18},"吃了今天的基础餐"),"water":({"health":2},"喝了一点水"),
 "pet":({"mood":5},"被温柔摸摸头"),"play":({"mood":8,"energy":-4},"和主人玩了一会儿"),
 "brush":({"cleanliness":12,"mood":4},"梳理了长毛"),"bath":({"cleanliness":25,"energy":-5},"完成虚拟清洁"),
 "litter":({"cleanliness":16},"猫砂盆打扫干净了"),"rest":({"energy":12,"health":1},"在暖窝休息"),
 "checkup":({"health":6},"完成游戏内健康照料")}
class LifeEngine:
    def __init__(self,path,clock=None,wall=None):
        self.path=Path(path);self.clock=clock or time.monotonic;self.wall=wall or time.time
        self.last_tick=self.clock();self.last_save=self.last_tick;self.cooldowns={};self.focus_deadline=None;self.error="";self.network_today=None
        self.data={"version":2,"birth_date":"2021-02-28","coins":150,"xp":0,"stats":dict(satiety=82,cleanliness=90,energy=85,mood=80,health=95),
          "inventory":{"fish":2,"bed":1,"bowl":1},"events":[],"diaries":{},"tasks":[],"mood_history":[],"badges":[],"daily":{},
          "age_override":None,"age_frozen":False,"scene":"desk","layouts":{},"layout_presets":{},
          "focus":{"duration":25,"remaining":1500,"active":False,"cycles":0},"travel":None,"postcards":[],
          "preferences":{"activity":60,"input_link":False,"cursor_chase":False,"sound":False,"volume":25,"diary_auto":False,"easter_eggs":True,
             "reminders":True,"weather":False,"latitude":0.0,"longitude":0.0,"d_day":"","network_time":False,"first_opened":False},
          "ai":{"enabled":False,"diary_enabled":False,"base_url":"https://api.openai.com/v1","model":"gpt-4.1-mini"},
          "last_wall":self.wall(),"effect":""}
        if self.path.exists():
            try:
                parsed=json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(parsed,dict):self._merge(self.data,parsed)
            except (OSError,ValueError) as exc:self.error="生活数据损坏，已回退默认值："+str(exc)
        self._validate()
        elapsed=max(0,min(8*3600,self.wall()-float(self.data.get("last_wall",self.wall()))))
        self._decay(elapsed,False);self.data["last_wall"]=self.wall()
        self.data["focus"]["active"]=False
    @staticmethod
    def _merge(target,source):
        for key in target:
            if key in source:
                if isinstance(target[key],dict) and isinstance(source[key],dict):LifeEngine._merge(target[key],source[key])
                elif isinstance(target[key],dict):continue
                else:target[key]=source[key]
        for key in ("inventory","diaries","layouts","layout_presets","daily"):
            if key in target and isinstance(source.get(key),dict):target[key]=source[key]
    def _validate(self):
        for key in STAT_NAMES:
            v=self.data["stats"].get(key,80)
            self.data["stats"][key]=max(0,min(100,float(v))) if isinstance(v,(int,float)) and math.isfinite(v) else 80
        for key in ("coins","xp"):
            v=self.data[key];self.data[key]=max(0,int(v)) if isinstance(v,(int,float)) and math.isfinite(v) else 0
        for key in ("events","tasks","mood_history","badges","postcards"):
            if not isinstance(self.data[key],list):self.data[key]=[]
        for key in ("inventory","diaries","layouts","layout_presets","daily"):
            if not isinstance(self.data[key],dict):self.data[key]={}
        for key,val in list(self.data["inventory"].items()):
            self.data["inventory"][key]=max(0,int(val)) if isinstance(val,(int,float)) and math.isfinite(val) else 0
        try:age_info(self.data["birth_date"],self.today())
        except (ValueError,TypeError):self.data["birth_date"]="2021-02-28"
        if self.data["scene"] not in SCENES:self.data["scene"]="desk"
        if not isinstance(self.data["age_override"],(int,float,type(None))):self.data["age_override"]=None
        if not isinstance(self.data["last_wall"],(int,float)) or not math.isfinite(self.data["last_wall"]):self.data["last_wall"]=self.wall()
        for k,default in (("activity",60),("volume",25)):
            v=self.data["preferences"].get(k);self.data["preferences"][k]=max(0,min(100,int(v))) if isinstance(v,(int,float)) and math.isfinite(v) else default
        for k in ("input_link","cursor_chase","sound","diary_auto","easter_eggs","reminders","weather","network_time","first_opened"):
            if not isinstance(self.data["preferences"].get(k),bool):self.data["preferences"][k]=False
        if not isinstance(self.data["preferences"].get("d_day"),str):self.data["preferences"]["d_day"]=""
        for k in ("enabled","diary_enabled"):
            if not isinstance(self.data["ai"].get(k),bool):self.data["ai"][k]=False
        for k,default in (("base_url","https://api.openai.com/v1"),("model","gpt-4.1-mini")):
            if not isinstance(self.data["ai"].get(k),str):self.data["ai"][k]=default
        v=self.data["age_override"]
        if v is not None and (not math.isfinite(v) or v<0 or v>=10000):self.data["age_override"]=None
        focus=self.data["focus"]
        for k,default in (("duration",25),("remaining",1500),("cycles",0)):
            v=focus.get(k);focus[k]=max(0,min(1000000,int(v))) if isinstance(v,(int,float)) and math.isfinite(v) else default
        trip=self.data["travel"]
        if trip is not None and (not isinstance(trip,dict) or not isinstance(trip.get("returns"),(int,float)) or not math.isfinite(trip["returns"]) or not isinstance(trip.get("place"),str)):self.data["travel"]=None
        self.data["tasks"]=[v for v in self.data["tasks"] if isinstance(v,dict) and isinstance(v.get("id"),str) and isinstance(v.get("text"),str) and isinstance(v.get("done"),bool)]
        self.data["events"]=[v for v in self.data["events"] if isinstance(v,dict) and all(isinstance(v.get(k),str) for k in ("at","day","kind","text"))][-5000:]
        self.data["mood_history"]=[v for v in self.data["mood_history"] if isinstance(v,dict) and isinstance(v.get("value"),(int,float)) and math.isfinite(v["value"])]
        self.data["diaries"]={k:v for k,v in self.data["diaries"].items() if isinstance(v,dict) and all(isinstance(v.get(f,""),str) for f in ("text","note","source"))}
        from .layout import valid_placement
        for scene,items in list(self.data["layouts"].items()):
            good=[]
            if isinstance(items,list):
                for item in items:
                    try:
                        if not isinstance(item,dict) or not isinstance(item.get("id"),str):continue
                        if not all(isinstance(item.get(k,1 if k=="scale" else 0),(int,float)) and math.isfinite(item.get(k,1 if k=="scale" else 0)) for k in ("x","z","scale","rotation")):continue
                        if .5<=item.get("scale",1)<=1.8 and valid_placement(item,good)[0]:good.append(item)
                    except (KeyError,TypeError,ValueError):continue
            self.data["layouts"][scene]=good
        self.data["postcards"]=[v for v in self.data["postcards"] if isinstance(v,dict) and isinstance(v.get("place"),str)]
        self.data["badges"]=[v for v in self.data["badges"] if isinstance(v,str)]
        self.data["layout_presets"]={k:v for k,v in self.data["layout_presets"].items() if isinstance(v,dict) and v.get("scene") in SCENES and isinstance(v.get("items"),list)}
    def today(self):return self.network_today or date.fromtimestamp(self.wall())
    def age(self):return age_info(self.data["birth_date"],self.today(),self.data["age_override"])
    @property
    def level(self):return 1+self.data["xp"]//100
    @property
    def mood(self):
        s=self.data["stats"]
        if s["energy"]<20:return "犯困"
        if s["satiety"]<20:return "委屈"
        if s["cleanliness"]<20:return "焦躁"
        if s["mood"]<25:return "低落"
        if s["mood"]<45:return "无聊"
        if s["mood"]<65:return "平静"
        if s["mood"]<85:return "开心"
        return "兴奋"
    def _decay(self,seconds,sleeping):
        h=max(0,seconds)/3600;s=self.data["stats"]
        s["satiety"]-=h*3;s["cleanliness"]-=h*1.4;s["energy"]+=h*(20 if sleeping else -3);s["mood"]-=h*1.5
        if s["satiety"]<10 or s["cleanliness"]<10:s["health"]-=h
        for k in s:s[k]=max(0,min(100,s[k]))
    def event(self,kind,text):
        self.data["events"].append({"at":datetime.fromtimestamp(self.wall()).isoformat(timespec="seconds"),"day":self.today().isoformat(),"kind":kind,"text":str(text)[:180]})
        self.data["events"]=self.data["events"][-5000:]
    def reward(self,coins=0,xp=0):self.data["coins"]+=coins;self.data["xp"]+=xp
    def care(self,kind):
        if kind not in CARE:return False,"未知照料项目"
        now=self.clock()
        if now-self.cooldowns.get(kind,-1e12)<20:return False,"刚刚照料过，陪年糕缓一会儿吧。"
        self.cooldowns[kind]=now
        effects,text=CARE[kind]
        for k,v in effects.items():self.data["stats"][k]=max(0,min(100,self.data["stats"][k]+v))
        self.reward(xp=2);self.event(kind,text);self.save();return True,text
    def can_buy(self,id):
        it=BY_ID.get(id)
        if not it:return False,"未知商品"
        if not it["ready"]:return False,it["note"]
        if not it["minimum"]<=self.age()["effective_months"]<it["maximum"]:return False,"不适合当前体验年龄"
        if self.data["coins"]<it["price"]:return False,"金币不足"
        return True,""
    def buy(self,id):
        ok,message=self.can_buy(id)
        if not ok:return False,message
        it=BY_ID[id]
        if it["kind"]=="import":return False,"请在设置中导入素材"
        self.data["coins"]-=it["price"];self.data["inventory"][id]=self.data["inventory"].get(id,0)+1
        self.event("purchase","购买了"+it["name"]);self.save();return True,"已放入背包"
    def use(self,id):
        it=BY_ID.get(id)
        if not it or self.data["inventory"].get(id,0)<1:return False,"背包中没有这件物品"
        if not it["ready"]:return False,it["note"]
        if not it["minimum"]<=self.age()["effective_months"]<it["maximum"]:return False,"不适合当前体验年龄"
        kind=it["kind"]
        if kind=="toy":
            now=self.clock()
            if now-self.cooldowns.get("toy",-1e12)<20:return False,"刚玩过玩具，让年糕休息一下"
            self.cooldowns["toy"]=now
        if kind=="furniture":return False,"请到家园中摆放"
        if kind=="room":self.data["scene"]=id.replace("room_","")
        elif kind=="age_freeze":self.data["age_override"]=self.age()["effective_months"];self.data["age_frozen"]=True
        elif kind=="age_kitten":self.data["age_override"]=6;self.data["age_frozen"]=True
        elif kind=="effect":self.data["effect"]=id
        elif kind not in ("consumable","toy"):return False,"此资源尚未适配"
        for k,v in it["effect"].items():self.data["stats"][k]=min(100,max(0,self.data["stats"][k]+v))
        if kind not in ("toy","room","effect"):self.data["inventory"][id]-=1
        self.event("use","使用了"+it["name"]);self.reward(xp=3);self.save();return True,"年糕很喜欢～"
    def scene_unlocked(self,scene):
        return scene=="desk" or (scene=="living" and self.level>=2) or (scene=="bedroom" and self.level>=3) or self.data["inventory"].get("room_"+scene,0)>0
    def set_scene(self,scene):
        if scene not in SCENES or not self.scene_unlocked(scene):return False,"空间尚未解锁"
        self.data["scene"]=scene;self.event("scene","去了"+SCENES[scene]);self.save();return True,"已切换空间"
    def add_task(self,text):
        text=text.strip()[:120]
        if not text:return False
        self.data["tasks"].append({"id":uuid.uuid4().hex,"text":text,"done":False,"day":self.today().isoformat()});self.save();return True
    def complete_task(self,id):
        for task in self.data["tasks"]:
            if task["id"]==id and not task["done"]:
                task["done"]=True;self.reward(5,5);self.event("task","完成待办："+task["text"]);self.save();return True
        return False
    def focus_start(self,minutes):
        minutes=max(1,min(180,int(minutes)));self.data["focus"].update(duration=minutes,remaining=minutes*60,active=True)
        self.focus_deadline=self.clock()+minutes*60;self.event("focus_start",f"开始{minutes}分钟专注")
    def focus_pause(self):
        if self.focus_deadline is not None:self.data["focus"]["remaining"]=max(0,math.ceil(self.focus_deadline-self.clock()))
        self.focus_deadline=None;self.data["focus"]["active"]=False
    def focus_resume(self):
        if self.data["focus"]["remaining"]>0:self.focus_deadline=self.clock()+self.data["focus"]["remaining"];self.data["focus"]["active"]=True
    def checkin(self):
        day=self.today().isoformat()
        if self.data["daily"].get("checkin")==day:return False,"今天已经打卡过啦"
        self.data["daily"]["checkin"]=day;self.reward(15,10);self.event("checkin","完成每日陪伴打卡");self.save();return True,"获得15金币"
    def unlock_badge(self,id):
        if not self.data["preferences"]["easter_eggs"] or id in self.data["badges"]:return False
        self.data["badges"].append(id);self.reward(10,10);self.event("badge","发现彩蛋："+id);self.save();return True
    def start_trip(self):
        if self.data["travel"]:return False,"年糕还在旅行中"
        self.data["travel"]={"returns":self.wall()+300,"place":random.choice(["窗边花园","午后书店","小鱼干集市"])}
        self.event("travel","开始一次五分钟虚拟旅行");self.save();return True,"五分钟后回来，桌宠仍可正常互动"
    def local_diary(self,day=None):
        day=day or self.today().isoformat();events=[e for e in self.data["events"] if e["day"]==day]
        body="今天我是年糕，鼻尖的小棕点也认真营业了。\n"
        body+="\n".join("· "+e["text"] for e in events[-8:]) if events else "今天还没有记下互动，不过安静陪着你也很好。"
        body+="\n今天的心情是"+self.mood+"。明天也想和你一起晒晒太阳。"
        old=self.data["diaries"].get(day,{})
        self.data["diaries"][day]={"text":body,"note":old.get("note",""),"source":"本地事件小结","updated":datetime.fromtimestamp(self.wall()).isoformat()}
        self.save();return body
    def tick(self,sleeping=False):
        now=self.clock();dt=max(0,min(300,now-self.last_tick));self.last_tick=now;self._decay(dt,sleeping);messages=[]
        if self.focus_deadline is not None:
            remain=max(0,math.ceil(self.focus_deadline-now));self.data["focus"]["remaining"]=remain
            if remain==0:
                self.focus_deadline=None;self.data["focus"]["active"]=False;self.data["focus"]["cycles"]+=1
                self.reward(20,20);self.event("focus_done","完成一轮专注");messages.append("专注完成！伸个懒腰，喝口水吧～")
        trip=self.data["travel"]
        if trip and self.wall()>=trip["returns"]:
            self.data["postcards"].append({"day":self.today().isoformat(),"place":trip["place"]});self.data["travel"]=None
            self.reward(12,10);self.event("postcard","带回了"+trip["place"]+"明信片");messages.append("旅行回来啦，给你带了明信片！")
        if now-self.last_save>=30:
            self.data["mood_history"].append({"at":self.wall(),"value":round(self.data["stats"]["mood"],2)})
            self.data["mood_history"]=self.data["mood_history"][-2880:];self.save();self.last_save=now
        return messages
    def save(self):
        temporary=None
        try:
            self.path.parent.mkdir(parents=True,exist_ok=True);self.data["last_wall"]=self.wall()
            with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",dir=self.path.parent,delete=False) as f:
                temporary=Path(f.name);json.dump(self.data,f,ensure_ascii=False,indent=2,allow_nan=False)
            os.replace(temporary,self.path);return True
        except (OSError,ValueError) as exc:
            self.error=str(exc)
            if temporary:temporary.unlink(missing_ok=True)
            return False
