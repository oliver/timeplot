#!/usr/bin/python


import sys
import math

from config import Cfg
from event import EventMgr
from base_reader import InputReader
from sdl_output import SdlOutput

from test_reader import *
from sys_linux_reader import *
from csv_reader import *

from debug import DBG


class SourceManager:
    def __init__ (self, store):
        self.store = store
        self.inputs = {}

    def sources (self):
        l = []
        for id in self.inputs:
            l.append( (id, self.inputs[id]['name']) )
        return l

    def register (self, name, unit=None):
        sourceId = len(self.inputs)
        self.inputs[sourceId] = {'name': name}
        self.store.onNewSource(sourceId)
        return sourceId

    def unregister (self, id):
        raise Exception("not yet implemented")


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

            if sourceData[0][0] > end or sourceData[-1][0] < start:
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

            result[id] = sourceData[i1:i2]
        return result


if __name__ == '__main__':
    # set up basic objects
    store = DataStore()
    sourceMgr = SourceManager(store)

    # start GUI
    widget = SdlOutput(None, store, sourceMgr)
    EventMgr.setImpl(widget)

    # add data sources
    testReader = TestFuncReader(sourceMgr, store, lambda t: math.sin(t), name="test: sin")
    testReader = TestFuncReader(sourceMgr, store, lambda t: math.sin(t) * 2.0, name="test: 2x sin")
    testReader = TestFuncReader(sourceMgr, store, lambda t: t - int(t), 50*1000, name="test: second fract.")

    try:
        reader = CpuLoadReader(sourceMgr, store)
    except:
        pass

    try:
        reader = NetIfReader(sourceMgr, store, 'eth0')
    except:
        pass

    # event data source
    testReader = TestFuncReader(sourceMgr, store, lambda t: int(t) % 2 == 0, 1000*1000, "test: events")

    args = sys.argv
    args.pop(0)
    if len(args) >= 2 and args[0] == '-c':
        Cfg.loadFile(args[1])
        args.pop(0); args.pop(0)

    for filename in args:
        reader = CsvReader(sourceMgr, store, filename)

    for r in Cfg.readers:
        if r.type == 'CsvReader':
            reader = CsvReader(sourceMgr, store, r.file)

    widget.run()
