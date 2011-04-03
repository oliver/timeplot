
import os
import time

from base_reader import InputReader
from event import EventMgr

class CpuLoadReader (InputReader):
    def __init__ (self, sourceMgr, store):
        InputReader.__init__(self, store)
        self.lastValues = None

        if not(os.path.isdir('/proc')):
            raise Exception("/proc directory not found")

        # order must match CPU field order in /proc/stat:
        self.ids = []
        self.ids.append( sourceMgr.register('CPU user') )
        self.ids.append( sourceMgr.register('CPU nice') )
        self.ids.append( sourceMgr.register('CPU system') )
        self.ids.append( sourceMgr.register('CPU idle') )

        EventMgr.startTimer(200*1000, self.onTimer)

    def onTimer (self):
        t = time.time()

        fd = open('/proc/stat')
        for l in fd:
            l = l.rstrip('\n')
            (name, value) = l.split(None, 1)
            if name == 'cpu':
                values = [int(x) for x in value.split()]
                values = values[:4]

                if self.lastValues is not None:
                    diffs = []
                    for i,v in enumerate(values):
                        diffs.append(v - self.lastValues[i])
                    fullTime = sum(diffs)
                    if fullTime > 0:
                        for i,d in enumerate(diffs):
                            percent = (float(d) / fullTime) * 100
                            self.store.update( (self.ids[i], t, percent) )
                self.lastValues = values
                break
        fd.close()
        return True

class NetIfReader (InputReader):
    def __init__ (self, sourceMgr, store, if_name):
        InputReader.__init__(self, store)
        self.targetIf = if_name

        self.lastData = {}

        if not(os.path.isfile('/proc/net/dev')):
            raise Exception("/proc/net/dev file not found")

        self.ids = {}
        self.ids['rBytes'] = sourceMgr.register(self.targetIf + ' bytes received', unit='bytes')
        self.ids['rPackets'] = sourceMgr.register(self.targetIf + ' packets received', unit='packets')
        self.ids['tBytes'] = sourceMgr.register(self.targetIf + ' bytes transmitted', unit='bytes')
        self.ids['tPackets'] = sourceMgr.register(self.targetIf + ' packets transmitted', unit='packets')

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
            self.store.update( (self.ids['rPackets'], t, allDiffs[self.targetIf][1]) )
            self.store.update( (self.ids['tPackets'], t, allDiffs[self.targetIf][9]) )
        return True

