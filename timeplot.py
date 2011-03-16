#!/usr/bin/python


import pygame
import time
import math

from event import EventMgr
from sdl_widgets import *
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
        self.widgets = []

        # TODO: move these into model:
        self.update = True
        self.endTime = time.time()
        self.displayedSeconds = 10

        pygame.init()

        self.scrollbar = SdlHScrollbar(10, 10, 400, 16, self.displayedSeconds, self.onScrollbarChanged)
        self.widgets.append(self.scrollbar)

        self.cbUpdate = SdlCheckbox(430, 10, "Update", self.onCbUpdateChanged)
        self.widgets.append(self.cbUpdate)
        self.cbUpdate.set(self.update)

    def onScrollbarChanged (self, widget):
        self.cbUpdate.set(False)
        self.endTime = self.scrollbar.getPos() + self.displayedSeconds

    def onCbUpdateChanged (self, widget):
        self.update = self.cbUpdate.checked()
        self.endTime = time.time()

    def startTimer (self, usec, callback):
        newId = self.lastId+1
        self.timers[newId] = callback
        pygame.time.set_timer(newId, int(usec / 1000.0))
        self.lastId = newId

    def run (self):
        width = 500
        height = 400

        self.screen = pygame.display.set_mode( (width, height), pygame.RESIZABLE)
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
                elif event.type == pygame.VIDEORESIZE:
                    (width, height) = event.size
                    self.screen = pygame.display.set_mode( (width, height), pygame.RESIZABLE)
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

                for w in self.widgets:
                    w.handleEvent(event)

            self.screen.fill( (0, 0, 0) )

            (availStart, availEnd) = self.store.getRange()
            self.scrollbar.setRange(availStart, availEnd)


            if self.update:
                nowTime = time.time()
                end = nowTime
                start = end - self.displayedSeconds
                self.scrollbar.setPos(start)
            else:
                end = self.endTime
                start = end - self.displayedSeconds


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

            yMin = -10
            yMax = 110
            yRange = yMax - yMin

            factorX = float(width)  / duration
            factorY = float(height) / yRange


            # draw grid
            font = pygame.font.Font(None, 18)
            for i in range(int(start), int(end)+2):
                x = (i - start) * factorX
                pygame.draw.line(self.screen, (64,64,64), (x,0), (x,height))

                if i % 5 == 0:
                    timeStr = time.strftime("%H:%M:%S", time.localtime(i))
                    surf = font.render(timeStr, True, (128,128,128))
                    self.screen.blit(surf, (x-(surf.get_width()/2), height-20))

            for i in xrange(yMin, yMax, 10):
                y = height - ((i - yMin) * factorY)
                color = (64,64,64)
                if i % 100 == 0:
                    color = (128,128,128)
                pygame.draw.line(self.screen, color, (0,y), (width,y))


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


            for w in self.widgets:
                w.draw(self.screen)

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
    
    reader = CpuLoadReader(store)
    sourceMgr.add(reader)

    widget.run()
