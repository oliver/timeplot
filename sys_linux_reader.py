
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

class NetIfReader (InputReader):
    def __init__ (self, store, ifName):
        InputReader.__init__(self, store)
        self.targetIf = ifName

        self.lastData = {}

        if not(os.path.isfile('/proc/net/dev')):
            raise Exception("/proc/net/dev file not found")

        EventMgr.startTimer(100*1000, self.onTimer)

    def onTimer (self):
        t = time.time()
        allDiffs = {}

        fd = open('/proc/net/dev')
        fd.readline() # first two lines contain headers
        fd.readline()

        for l in fd:
            l = l.rstrip('\n')
            l = l.lstrip(' ')
            (ifName, data) = l.split(':', 1)

            intData = []
            for s in data.split():
                intData.append(int(s))

#            (rBytes, rPackets, rErrors, rDrop, rFifo, rFrame, rComp, rMcast,
#             tBytes, tPackets, tErrors, tDrop, tFifo, tColls, tCarrier, tComp) = intData
#            print rBytes, tBytes
            
            if self.lastData.has_key(ifName):
                diff = []
                for i,v in enumerate(self.lastData[ifName]):
                    diff.append(intData[i] - v)
                    assert(diff[i] >= 0) # TODO: handle overflow
                allDiffs[ifName] = diff

            self.lastData[ifName] = intData
        fd.close()

        #print allDiffs

        if allDiffs.has_key(self.targetIf):
            self.store.update( (self.id, t, allDiffs[self.targetIf][1]) )
        return True

