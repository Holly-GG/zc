"""Quiet stationary photo poses, independent of roaming and chat schedules."""
import random,time
class WorkIdle:
    POSES=('idle','bored','tail_sway','ear_flick','lick_paw','groom','yawn','expectant')
    def __init__(self,rng=None,clock=time.monotonic):
        self.rng=rng or random.Random();self.clock=clock;self.pose='idle';self.started=clock();self.deadline=self.started;self.previous=None
    def reset(self):
        now=self.clock();self.pose=self.rng.choice(self.POSES);self.previous=self.pose;self.started=now;self.deadline=now+self.rng.uniform(5,9)
    def sample(self,counts,now=None):
        now=self.clock() if now is None else now
        if now>=self.deadline:
            if self.pose!='idle':self.pose='idle';duration=self.rng.uniform(24,48)
            else:
                choices=[p for p in self.POSES if p!=self.previous and p in counts]
                self.pose=self.rng.choice(choices or ['idle']);self.previous=self.pose;duration=self.rng.uniform(5,9)
            self.started=now;self.deadline=now+duration
        count=counts.get(self.pose,1);frame=int(max(0,now-self.started)*1.8)%count
        return self.pose,frame
