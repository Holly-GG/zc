"""Monotonic, interruptible action sequences. Never modifies the OS cursor."""
from collections import deque
import random,time
from .actions import ACTIONS,MOOD_POOLS
class Director:
    def __init__(self,clock=None,rng=None):
        self.clock=clock or time.monotonic;self.rng=rng or random.Random();self.queue=deque();self.deadline=0;self.active=False
        self.next_auto=self.clock()+12;self.last_trigger={};self.override=None;self.rate=1.
    def set_rate(self,rate):
        rate=max(.01,min(1.,rate))
        if rate!=self.rate:self.next_auto=self.clock()+max(0,self.next_auto-self.clock())*self.rate/rate;self.rate=rate
    def cancel(self):self.queue.clear();self.active=False
    def sequence(self,steps,play):
        self.cancel();self.queue.extend(steps);return self._advance(play)
    def _advance(self,play):
        while self.queue:
            key,seconds=self.queue.popleft()
            if key in ACTIONS and play(key,seconds):
                self.deadline=self.clock()+seconds;self.active=True;return key
        self.active=False;return None
    def tick(self,play,paused=False):
        if not paused and self.active and self.clock()>=self.deadline:return self._advance(play)
        return None
    def ready(self,kind,seconds):
        now=self.clock()
        if now-self.last_trigger.get(kind,-1e12)<seconds:return False
        self.last_trigger[kind]=now;return True
    def mood(self,normal):return self.override or normal
    def auto(self,normal,play,allowed=True):
        now=self.clock()
        if not allowed or self.active or now<self.next_auto:return None
        self.next_auto=now+self.rng.uniform(12,25)/self.rate
        return self.sequence([(self.rng.choice(MOOD_POOLS.get(self.mood(normal),MOOD_POOLS["平静"])),4)],play)
    def stroke(self,play):
        return self.sequence([("pet",1.4),(self.rng.choice(["knead","rub_hand","purr_eyes","roll"]),3.5)],play)
    def poke(self,play):
        return self.sequence([(self.rng.choice(["startle_jump","angry_shake","ignore","puff"]),2.4),("ear_flick",1.8)],play)
    def feed(self,play):return self.sequence([("feed",3),("mouth_lick",1.8),("leg_rub",2.5)],play)
    def tease(self,play):return self.sequence([("hunt_wiggle",2.4),("pounce",1.6),("dodge",2),("swat",2.4)],play)
    def chase(self,play,success=False):
        return self.sequence([("stalk",2),("hunt_wiggle",1.8),("pounce",1.2),("cursor_trophy" if success else "miss",2.5)],play)
