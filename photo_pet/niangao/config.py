from pathlib import Path
import json, os, tempfile, math

DEFAULTS={"name":"年糕","width":240,"always_on_top":True,"position":None,"roaming":True,"work_mode":False,"work_position":None,"work_panel_position":None,"focus_position":None}

def config_path():
    return Path(os.environ.get("APPDATA", str(Path.home()/".config")))/"NiangaoPhotoPet"/"settings.json"

class Settings:
    def __init__(self, path=None):
        self.path=Path(path) if path else config_path()
        self.data=DEFAULTS.copy()
        self.error=""
        try:
            if self.path.exists():
                parsed=json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(parsed,dict): raise ValueError("settings must be an object")
                self.data.update({k:v for k,v in parsed.items() if k in DEFAULTS})
        except (OSError,ValueError) as exc: self.error=str(exc)
        width=self.data["width"]
        if not isinstance(width,(int,float)) or not math.isfinite(width): width=240
        self.data["width"]=int(max(80,min(420,width)))
        for key in ("always_on_top","roaming","work_mode"):
            if not isinstance(self.data[key],bool): self.data[key]=DEFAULTS[key]
        for key in ("position","work_position","work_panel_position","focus_position"):
            pos=self.data[key]
            if not (isinstance(pos,list) and len(pos)==2 and all(isinstance(v,(int,float)) and math.isfinite(v) for v in pos)):self.data[key]=None

    def save(self):
        temporary=None
        try:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",dir=self.path.parent,delete=False) as file:
                temporary=Path(file.name)
                json.dump(self.data,file,ensure_ascii=False,indent=2)
            os.replace(temporary,self.path)
            return True
        except OSError as exc:
            self.error=str(exc)
            if temporary: temporary.unlink(missing_ok=True)
            return False
