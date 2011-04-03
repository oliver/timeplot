
import time
import math

from base_reader import InputReader
from event import EventMgr

class TestFuncReader (InputReader):
    def __init__ (self, sourceMgr, store, function, interval=100*1000, name="test"):
        InputReader.__init__(self, store)

        self.codeObj = compile(function, '<string>', 'eval')
        eval(self.codeObj, None, {'t':0}) # check if supplied code is basically ok

        self.id = sourceMgr.register(name)

        EventMgr.startTimer(interval, self.onTimer)

    def onTimer (self):
        t = time.time()
        value = eval(self.codeObj)
        self.store.update( (self.id, t, value) )
        return True

