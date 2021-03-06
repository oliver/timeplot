#!/usr/bin/python


import sys
import math
import getopt
import time

from config import Cfg
from event import EventMgr
from loader import ReaderLoader
from base_reader import InputReader

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

        self.reportingInterval = 0.05 # combine changes of N seconds into one update event
        self.updateHandlers = []

        self.lastUpdateEvent = 0
        self.dirtyStart = None
        self.dirtyEnd = None

    def onNewSource (self, id):
        assert(not(self.data.has_key(id)))
        self.data[id] = []

    def registerUpdateHandler (self, handlerFunc):
        self.updateHandlers.append(handlerFunc)
        self.lastUpdateEvent = 0 # force flushing of current update events

    def update (self, tup):
        (id, timestamp, value) = tup
        #print "data update from source '%s'" % id
        self.data[id].append( (timestamp, value) )

        if self.oldest is None or timestamp < self.oldest:
            self.oldest = timestamp
        if self.newest is None or timestamp > self.newest:
            self.newest = timestamp

        if self.updateHandlers:
            endTime = timestamp
            if len(self.data[id]) == 1:
                startTime = endTime
            else:
                startTime = self.data[id][-2][0]

            if self.dirtyStart is None or startTime < self.dirtyStart:
                self.dirtyStart = startTime
            if self.dirtyEnd is None or endTime > self.dirtyEnd:
                self.dirtyEnd = endTime

            nowTime = time.time()
            if self.lastUpdateEvent + self.reportingInterval < nowTime:
                for func in self.updateHandlers:
                    func(self.dirtyStart, self.dirtyEnd)

                self.lastUpdateEvent = nowTime
                self.dirtyStart = None
                self.dirtyEnd = None

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


def Usage ():
    print "%s [-c <config file>] [--csv <CSV file>] [--ui <sdl|qt>]" % sys.argv[0]


if __name__ == '__main__':
    configFile = None
    csvFiles = []
    uiType = 'sdl'

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:', ['cfg=', 'csv=', 'ui='])
    except getopt.GetoptError, err:
        print str(err)
        Usage()
        sys.exit(1)
    for o, a in opts:
        if o == '-c' or o == '--cfg':
            configFile = a
        elif o == '--csv':
            csvFiles.append(a)
        elif o == '--ui':
            uiType = a
        else:
            raise Exception('unknown option "%s"' % o)

    if not(configFile) and not(csvFiles):
        Usage()
        sys.exit(1)

    if configFile:
        Cfg.loadFile(configFile)

    # set up basic objects
    store = DataStore()
    sourceMgr = SourceManager(store)

    # start GUI
    if uiType == 'sdl':
        from sdl_output import SdlOutput
        widget = SdlOutput(None, store, sourceMgr)
    elif uiType == 'qt':
        from qt_output import QtOutput
        widget = QtOutput(store, sourceMgr)
    else:
        print "invalid UI type '%s'" % uiType
        Usage()
        sys.exit(1)

    EventMgr.setImpl(widget)

    for filename in csvFiles:
        reader = CsvReader(sourceMgr, store, filename)

    loader = ReaderLoader()

    for r in Cfg.readers:
        classObj = loader.load(r.type)
        if not(classObj):
            print "unknown reader type '%s'" % r.type
        else:
            try:
                funcArgs = {}
                for k,v in r.copy().items():
                    funcArgs[str(k)] = v
                del funcArgs['type']
                reader = classObj(sourceMgr, store, **funcArgs)
            except Exception, e:
                print "could not load reader '%s' (%s)" % (r.type, e)

    widget.run()
