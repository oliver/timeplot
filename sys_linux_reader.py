
import os
import time

from base_reader import InputReader
from event import EventMgr

class CpuLoadReader (InputReader):
    def __init__ (self, store):
        InputReader.__init__(self, store)
        self.lastCpu = None
        self.lastIdle = None

        if not(os.path.isdir('/proc')):
            raise Exception("/proc directory not found")

        EventMgr.startTimer(200*1000, self.onTimer)

    def onTimer (self):
        t = time.time()

        percent = None
        fd = open('/proc/stat')
        for l in fd:
            l = l.rstrip('\n')
            (name, value) = l.split(None, 1)
            if name == 'cpu':
                values = [int(x) for x in value.split()]
                (tUser, tNice, tKernel, tIdle) = values[:4]
                tCpu = tUser + tNice + tKernel

                if self.lastCpu is not None:
                    dCpu = tCpu - self.lastCpu
                    dIdle = tIdle - self.lastIdle
                    if dCpu+dIdle > 0:
                        percent = (float(dCpu) / (dCpu+dIdle)) * 100.0
                self.lastCpu = tCpu
                self.lastIdle = tIdle

                break
        fd.close()

        if percent is not None:
            self.store.update( (self.id, t, percent) )
        return True

