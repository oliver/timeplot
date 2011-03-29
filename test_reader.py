
import time

from base_reader import InputReader
from event import EventMgr

class TestFuncReader (InputReader):
    def __init__ (self, sourceMgr, store, func, interval=100*1000, name="test"):
        "func gets the current time as parameter and must return a value"
        InputReader.__init__(self, store)
        self.func = func
        self.id = sourceMgr.register(name)

        EventMgr.startTimer(interval, self.onTimer)

    def onTimer (self):
        t = time.time()
        value = self.func(t)
        self.store.update( (self.id, t, value) )
        return True

