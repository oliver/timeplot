#!/usr/bin/python


import sys
import math

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

    def add (self, reader):
        sourceId = len(self.inputs)
        self.inputs[sourceId] = reader
        reader.setId(sourceId)
        self.store.onNewSource(sourceId)

    def start (self):
        for sourceId,reader in self.inputs.items():
            reader.start()


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
    widget = SdlOutput(None, store)
    EventMgr.setImpl(widget)

    # add data sources
    testReader = TestFuncReader(store, lambda t: math.sin(t) )
    sourceMgr.add(testReader)
    testReader = TestFuncReader(store, lambda t: math.sin(t) * 2.0 )
    sourceMgr.add(testReader)
    testReader = TestFuncReader(store, lambda t: t - int(t), 50*1000)
    sourceMgr.add(testReader)

    try:
        reader = CpuLoadReader(store)
        sourceMgr.add(reader)
    except:
        pass

    # event data source
    testReader = TestFuncReader(store, lambda t: int(t) % 2 == 0, 1000*1000)
    sourceMgr.add(testReader)

    for filename in sys.argv[1:]:
        reader = CsvReader(store, filename)
        sourceMgr.add(reader)

    sourceMgr.start()
    widget.run()
