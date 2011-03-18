#!/usr/bin/python


import sys
import time
import math

from event import EventMgr
from sdl_output import SdlOutput
from csv_reader import *
from debug import DBG


class SourceManager:
    def __init__ (self, store):
        self.store = store
        self.inputs = {}

    def add (self, reader):
        sourceId = len(self.inputs)
        self.inputs[sourceId] = reader
        reader.setId(sourceId)
        self.store.onNewSource(sourceId)

    def start (self):
        for sourceId,reader in self.inputs.items():
            reader.start()


class InputReader:
    def __init__ (self, store):
        self.store = store
        self.id = None

    def setId (self, id):
        self.id = id

    def start (self):
        pass


class TestReader (InputReader):
    def __init__ (self, store):
        InputReader.__init__(self, store)

        self.i = 0
        EventMgr.startTimer(100*1000, self.onTimer)

    def onTimer (self):
        #print "timer"
        t = time.time()
        #value = self.i
        #value = self.i * self.i
        #value = math.sin(self.i / 2.0) * 10.0
        value = math.sin(t) * 10.0
        #value = t - int(t)
        self.store.update( (self.id, t, value) )
        self.i += 1
        return True


class TestFuncReader (InputReader):
    def __init__ (self, store, func, interval=100*1000):
        "func gets the current time as parameter and must return a value"
        InputReader.__init__(self, store)
        self.func = func

        EventMgr.startTimer(interval, self.onTimer)

    def onTimer (self):
        t = time.time()
        value = self.func(t)
        self.store.update( (self.id, t, value) )
        return True


class CpuLoadReader (InputReader):
    def __init__ (self, store):
        InputReader.__init__(self, store)
        self.lastCpu = None
        self.lastIdle = None

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



class DataStore:
    def __init__ (self):
        self.data = {}
        self.oldest = None
        self.newest = None

    def onNewSource (self, id):
        assert(not(self.data.has_key(id)))
        self.data[id] = []

    def update (self, tup):
        (id, time, value) = tup
        #print "data update from source '%s'" % id
        self.data[id].append( (time, value) )

        if self.oldest is None or time < self.oldest:
            self.oldest = time
        if self.newest is None or time > self.newest:
            self.newest = time

    def getRange (self):
        return (self.oldest, self.newest)

    def get (self, start, end):
        "returns dict of lists of tuples"
        result = {}
        for id in self.data:
            sourceData = self.data[id]
            if not(sourceData):
                result[id] = []
                continue

            def search (data, time):
                """
                Returns a tuple of two indexes; first is the index of the item before the requested time,
                second is the index of the item after (or exactly at) the requested time.
                Either value can be None (if there is no such index).
                """

                # binary search:
                lo = 0
                hi = len(data)
                while lo < hi:
                    mid = (lo+hi) // 2
                    midVal = data[mid]
                    t = midVal[0]
                    if t < time:
                        lo = mid + 1
                    elif t > time:
                        hi = mid
                    else:
                        # exact match
                        lo = mid
                        hi = mid
                        break

                # target is now somewhere between (inclusive) lo-1 and hi+1:
                lo = max(0, lo-2)
                hi = min(len(data), hi+2)

                prevIndex = None
                for i in range(lo, hi):
                    tup = data[i]
                    t = tup[0]
                    if t >= time:
                        return (prevIndex, i)
                    prevIndex = i
                return (prevIndex, None)

            firstIndex = search(sourceData, start)
            lastIndex = search(sourceData, end)

            i1 = firstIndex[1]
            if i1 is None:
                i1 = firstIndex[0]
            assert(i1 is not None)

            i2 = lastIndex[1]
            if i2 is None:
                i2 = lastIndex[0]
            assert(i2 is not None)

            i1 = max(0, i1-1)
            i2 = min(len(sourceData), i2+1)

            l = []
            for i in range(i1, i2):
                tup = sourceData[i]
                l.append(tup)
            result[id] = l
        return result


if __name__ == '__main__':
    # set up basic objects
    store = DataStore()
    sourceMgr = SourceManager(store)

    # start GUI
    widget = SdlOutput(None, store)
    EventMgr.setImpl(widget)

    # add data sources
    testReader = TestFuncReader(store, lambda t: math.sin(t) )
    sourceMgr.add(testReader)
    testReader = TestFuncReader(store, lambda t: math.sin(t) * 2.0 )
    sourceMgr.add(testReader)
    testReader = TestFuncReader(store, lambda t: t - int(t), 50*1000)
    sourceMgr.add(testReader)
    
    reader = CpuLoadReader(store)
    sourceMgr.add(reader)

    # event data source
    testReader = TestFuncReader(store, lambda t: int(t) % 2 == 0, 1000*1000)
    sourceMgr.add(testReader)

    for filename in sys.argv[1:]:
        reader = CsvReader(store, filename)
        sourceMgr.add(reader)

    sourceMgr.start()
    widget.run()
