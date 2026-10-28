"""Unattended proactive frequency is 30% of the former rate, never slower care timers."""
import time
PASSIVE_RATE=.30
ACTIVE_SECONDS=20.
class AutonomyPolicy:
    def __init__(self,clock=None):self.clock=clock or time.monotonic;self.last_click=None
    def click(self):self.last_click=self.clock()
    @property
    def rate(self):
        return 1. if self.last_click is not None and 0<=self.clock()-self.last_click<ACTIVE_SECONDS else PASSIVE_RATE
    def interval(self,former_seconds):return former_seconds/self.rate
