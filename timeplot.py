#!/usr/bin/python


import pygame
import time
import math

from event import EventMgr
from debug import DBG


class BaseOutput:
    def __init__ (self, model):
        self.model = model


    def startTimer (self, usec, callback):
        raise Exception("not implemented")

    def watchFd (self, fd, callback):
        raise Exception("not implemented")


    def onUpdate (self):
        pass



class SdlOutput(BaseOutput):
    def __init__ (self, model, store):
        BaseOutput.__init__(self, model)
        self.store = store

        self.lastId = pygame.USEREVENT
        self.timers = {}

        pygame.init()


    def startTimer (self, usec, callback):
        newId = self.lastId+1
        self.timers[newId] = callback
        pygame.time.set_timer(newId, int(usec / 1000.0))
        self.lastId = newId

    def run (self):
        width = 500
        height = 400

        self.screen = pygame.display.set_mode( (width, height), 0)
        self.clock = pygame.time.Clock()
        print "starting"
        while True:

            # TODO: timer resolution is now tied to the Hz value here;
            # it might be better if timers and fd watchers are independent of any static update rate.
            timePassed = self.clock.tick(30)
            
            for event in pygame.event.get():
                #print event
                if event.type == pygame.QUIT:
                    return
                else:
                    if self.timers.has_key(event.type):
                        cb = self.timers[event.type]
                        ret = cb()
                        if not(ret):
                            pygame.time.set_timer(event.type, 0)
                            self.timers[event.type] = None
                    else:
                        #DBG.brk()
                        pass

            self.screen.fill( (0, 0, 0) )

            nowTime = time.time()
            end = nowTime
            start = end - 10

#             (start, end) = self.store.getRange()
#             if start is None:
#                 start = time.time()
#                 end = time.time()
#             if (start - end) < 2.1:
#                 start = end - 2.1
            duration = end - start
            #print start, end

            allPoints = self.store.get(start, end)
            #print allPoints

            yMin = -3
            yMax = 3
            yRange = yMax - yMin

            factorX = float(width)  / duration
            factorY = float(height) / yRange

            for id,l in allPoints.items():
                #print len(l)
                points = []
                for e in l:
                    t = e[0]
                    value = e[1]
                    x = (t - start) * factorX
                    y = height - ((value - yMin) * factorY)
                    points.append( (x,y) )
                if len(points) > 1:
                    pygame.draw.lines(self.screen, (255,255,255), False, points)


            #print self.clock.get_fps()
            pygame.display.flip()



class SourceManager:
    def __init__ (self, store):
        self.store = store
        self.inputs = {}

    def add (self, reader):
        sourceId = len(self.inputs)
        self.inputs[sourceId] = reader
        reader.setId(sourceId)
        self.store.onNewSource(sourceId)


class InputReader:
    def __init__ (self, store):
        self.store = store
        self.id = None

    def setId (self, id):
        self.id = id


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
            l = []
            prevTuple = None
            for tup in self.data[id]:
                t = tup[0]
                if t >= start and t <= end:
                    if not(l) and prevTuple is not None:
                        # always add one earlier than requested:
                        l.append(prevTuple)
                    l.append(tup)
                prevTuple = tup
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

    widget.run()
