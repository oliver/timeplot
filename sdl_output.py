
import pygame
import time

from base_output import *
from sdl_widgets import *


class SdlOutput(BaseOutput):
    def __init__ (self, model, store):
        BaseOutput.__init__(self, model)
        self.store = store

        self.lastId = pygame.USEREVENT
        self.timers = {}
        self.widgets = []

        # TODO: move these into model:
        self.showAll = False
        self.update = True
        self.endTime = time.time()
        self.displayedSeconds = 10

        pygame.init()

        self.scrollbar = SdlHScrollbar(10, 10, 400, 16, self.displayedSeconds, 3, self.onScrollbarChanged)
        self.widgets.append(self.scrollbar)

        self.cbUpdate = SdlCheckbox(430, 10, "Update", self.onCbUpdateChanged)
        self.widgets.append(self.cbUpdate)
        self.cbUpdate.set(self.update)

        self.cbShowAll = SdlCheckbox(10, 40, "Show All", self.onCbShowAllChanged)
        self.widgets.append(self.cbShowAll)
        self.cbShowAll.set(self.showAll)

    def onScrollbarChanged (self, widget):
        self.cbUpdate.set(False)
        self.endTime = self.scrollbar.getPos() + self.displayedSeconds

    def onCbUpdateChanged (self, widget):
        self.update = self.cbUpdate.checked()
        self.endTime = time.time()

    def onCbShowAllChanged (self, widget):
        self.showAll = self.cbShowAll.checked()
        self.scrollbar.setVisibility(not(self.showAll))
        self.cbUpdate.setVisibility(not(self.showAll))

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
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
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

                for w in self.widgets:
                    w.handleEvent(event)

            self.screen.fill( (0, 0, 0) )

            nowTime = time.time()

            (availStart, availEnd) = self.store.getRange()
            if availStart is None:
                availStart = nowTime
            if availEnd is None:
                availEnd = nowTime

            if self.showAll:
                start = availStart
                end = availEnd
            elif self.update:
                end = nowTime
                start = end - self.displayedSeconds
                self.scrollbar.setPos(start)
            else:
                end = self.endTime
                start = end - self.displayedSeconds

            posEnd = max(availEnd, end, nowTime)
            self.scrollbar.setRange(availStart, posEnd)

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
                if not(l):
                    continue
                if type(l[0][1]) == bool:
                    # event data
                    for e in l:
                        t = e[0]
                        value = e[1]
                        if value:
                            x = (t - start) * factorX
                            pygame.draw.line(self.screen, (255,255,255), (x,0), (x,height))
                else:
                    # value data
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

