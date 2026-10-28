"""Offline illustrative synthesis, NOT a recording of Niangao. Windows async WAV."""
import math,random,time,wave,struct,sys
from pathlib import Path
from .actions import SOUNDS
RATE=22050
def synthesize(kind,volume=25):
    if kind not in SOUNDS:raise ValueError("Unknown sound")
    duration={"milk_meow":.65,"adult_meow":.85,"senior_meow":1.0,"purr":1.1,"smack":.45,"hiss":.55,"scratch":.7,"bell":.8,"snore":1.3}[kind]
    rng=random.Random(kind);result=bytearray();phase=0;gain=max(0,min(100,volume))/100*.6
    for i in range(int(RATE*duration)):
        t=i/RATE;u=t/duration;env=min(1,t/.025,(duration-t)/.045)
        if kind in ("milk_meow","adult_meow","senior_meow"):
            f={"milk_meow":680,"adult_meow":440,"senior_meow":260}[kind]*(1+.36*math.sin(math.pi*u)-.30*u)
            phase+=2*math.pi*f/RATE
            value=(math.sin(phase)+.34*math.sin(phase*2)+.18*math.sin(phase*3))*.55*math.sin(math.pi*u)**.5
        elif kind=="purr":value=(rng.uniform(-1,1)*.28+math.sin(2*math.pi*92*t)*.14)*(.5+.5*math.sin(2*math.pi*27*t))
        elif kind=="snore":value=(math.sin(2*math.pi*82*t)*.25+rng.uniform(-1,1)*.15)*math.sin(math.pi*u)**2*(.6+.4*math.sin(2*math.pi*24*t))
        elif kind=="bell":value=sum(math.sin(2*math.pi*f*t)*a for f,a in [(1046,.4),(2092,.2),(2810,.12)])*math.exp(-5*u)
        elif kind=="hiss":value=rng.uniform(-1,1)*.55*math.sin(math.pi*u)
        elif kind=="scratch":value=rng.uniform(-1,1)*max(0,math.sin(2*math.pi*8*t))*.5
        else:value=(rng.uniform(-1,1)*.6+math.sin(2*math.pi*190*t)*.15)*max(0,math.sin(2*math.pi*7*t))**8
        result.extend(struct.pack("<h",int(max(-1,min(1,value*env*gain))*32767)))
    return bytes(result)
class SoundPlayer:
    def __init__(self,directory,preferences,clock=None,backend=None):
        self.directory=Path(directory);self.preferences=preferences;self.clock=clock or time.monotonic;self.last=-1e12;self.error="";self.backend=backend
        if backend is None and sys.platform=="win32":
            import winsound
            self.backend=lambda path:winsound.PlaySound(str(path) if path else None,winsound.SND_FILENAME|winsound.SND_ASYNC|winsound.SND_NODEFAULT)
    @property
    def supported(self):return self.backend is not None
    def play(self,kind,force=False):
        if kind not in SOUNDS or not self.preferences.get("sound") or self.preferences.get("volume",0)<=0 or not self.backend:return False
        now=self.clock()
        if not force and now-self.last<1.5:return False
        volume=max(0,min(100,round(self.preferences["volume"]/10)*10))
        if volume==0:return False
        try:
            path=self.directory/(kind+"-"+str(volume)+".wav")
            if not path.exists():
                self.directory.mkdir(parents=True,exist_ok=True)
                with wave.open(str(path),"wb") as f:f.setparams((1,2,RATE,0,"NONE","not compressed"));f.writeframes(synthesize(kind,volume))
            self.backend(path);self.last=now;return True
        except (OSError,RuntimeError,ValueError):self.error="音效播放不可用";return False
    def stop(self):
        if self.backend:
            try:self.backend(None)
            except (OSError,RuntimeError):pass
