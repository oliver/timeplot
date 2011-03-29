
import pygame
import time
import datetime

from base_output import *
from sdl_widgets import *


class SdlOutput(BaseOutput):
    def __init__ (self, model, store, sourceMgr):
        BaseOutput.__init__(self, model)
        self.store = store
        self.sourceMgr = sourceMgr

        self.lastId = pygame.USEREVENT
        self.timers = {}
        self.widgets = []

        # TODO: move these into model:
        self.showAll = False
        self.update = True
        self.endTime = time.time()
        self.displayedSeconds = 10
        
        self.start = None
        self.end = None

        self.zooming = False
        self.panning = False

        self.width = 800
        self.height = 600

        # create list of possible X grid intervals:
        self.floatFactorLength = 3
        self.floatFactor = 10 ** self.floatFactorLength

        self._xIntervals = []
        for sec in [0.25, 0.5, 1, 5, 10]:
            sec *= self.floatFactor
            self._xIntervals.append(sec)
            self._xIntervals.append(int(sec*60))
            self._xIntervals.append(int(sec*60*60))
        for sec in [0.01, 0.05, 0.1, 0.2]:
            self._xIntervals.append(sec * self.floatFactor)
        for hour in [1, 3, 6, 12, 24, 24*2, 24*7, 24*30, 24*30*2, 24*30*6, 24*365]:
            self._xIntervals.append(hour * 60*60 * self.floatFactor)
        self._xIntervals.sort()

        pygame.init()

        self.scrollbar = SdlHScrollbar(10, 10, 400, 16, self.displayedSeconds, 3, self.onScrollbarChanged)
        self.widgets.append(self.scrollbar)

        self.cbUpdate = SdlCheckbox(430, 10, "Update", self.onCbUpdateChanged)
        self.widgets.append(self.cbUpdate)
        self.cbUpdate.set(self.update)

        self.cbShowAll = SdlCheckbox(10, 40, "Show All", self.onCbShowAllChanged)
        self.widgets.append(self.cbShowAll)
        self.cbShowAll.set(self.showAll)

        self.lblCurrent = SdlLabel(10, 70)
        self.widgets.append(self.lblCurrent)
        
        self.lblDebug = SdlLabel(10, 100)
        self.widgets.append(self.lblDebug)

    def onScrollbarChanged (self, widget):
        self.cbUpdate.set(False)
        self.endTime = self.scrollbar.getPos() + self.displayedSeconds
        self._setRange()

    def onCbUpdateChanged (self, widget):
        self.update = self.cbUpdate.checked()
        if self.update:
            self.displayedSeconds = 10
        self.endTime = time.time()
        self._setRange()

    def onCbShowAllChanged (self, widget):
        self.showAll = self.cbShowAll.checked()
        self.scrollbar.setVisibility(not(self.showAll))
        self.cbUpdate.setVisibility(not(self.showAll))
        self._setRange()

    def onCbSourceToggled (self, widget):
        # TODO: the callback should also provide user-defined parameters
        for id,m in self.sourceLabels.items():
            if m['widget'] == widget:
                m['visible'] = widget.checked()
                break

    def startTimer (self, usec, callback):
        newId = self.lastId+1
        self.timers[newId] = callback
        pygame.time.set_timer(newId, int(usec / 1000.0))
        self.lastId = newId

    def _roundXInterval (self, target):
        bestInterval = self._xIntervals[0]
        bestDiff = None
        for interval in self._xIntervals:
            diff = abs(target-interval)
            if bestDiff is None or diff < bestDiff:
                bestInterval = interval
                bestDiff = diff
        return bestInterval

    def _setRange (self):
        if not(self.showAll) and not(self.update):
            self.end = self.endTime
            self.start = self.end - self.displayedSeconds

    def _xToPos (self, sx):
        duration = self.end - self.start
        factorX = float(self.width) / duration
        px = (sx / factorX) + self.start
        return px

    def _xToScreen (self, px):
        duration = self.end - self.start
        factorX = float(self.width) / duration
        sx = (px - self.start) * factorX
        return sx


    def run (self):
        self.screen = pygame.display.set_mode( (self.width, self.height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

        # TODO: react to sources added at runtime
        self.sourceLabels = {}
        x = self.width - 200
        y = 10
        for (id, sourceName) in self.sourceMgr.sources():
            label = SdlCheckbox(x, y, sourceName, self.onCbSourceToggled)
            label.set(True)
            self.sourceLabels[id] = {'widget': label, 'visible': True}
            self.widgets.append(label)
            y += 30

        print "starting"
        while True:

            # TODO: timer resolution is now tied to the Hz value here;
            # it might be better if timers and fd watchers are independent of any static update rate.
            timePassed = self.clock.tick(30)

            for event in pygame.event.get():
                handled = False
                for w in reversed(self.widgets):
                    if w.handleEvent(event):
                        # event was handled by this widget
                        handled = True
                        break

                if handled:
                    continue

                #print event
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.VIDEORESIZE:
                    (self.width, self.height) = event.size
                    self.screen = pygame.display.set_mode( (self.width, self.height), pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # start zoom
                    if event.button == 1:
                        self.zooming = True
                        self.panning = False
                        self.zoomStart = event.pos
                        self.zoomEnd = event.pos
                        pygame.mouse.set_cursor(*pygame.cursors.diamond)
                    if event.button == 2:
                        self.panning = True
                        self.zooming = False
                        pygame.mouse.set_cursor(*pygame.cursors.broken_x)
                        self.panStartX = event.pos[0]
                        self.panStartTime = self.start
                        savedStart = self.start
                        savedEnd = self.end
                        self.cbUpdate.set(False)
                        self.cbShowAll.set(False)
                        self.start = savedStart
                        self.end = savedEnd
                        self.displayedSeconds = self.end - self.start
                        self.scrollbar.setPageWidth(self.displayedSeconds)
                    elif event.button == 4 and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        # zoom in
                        oldDuration = self.end - self.start
                        newDuration = oldDuration / 2.0
                        diff = oldDuration - newDuration
                        if diff > 0.1: # show at least 100 ms
                            halfDiff = diff / 2.0
                            newStart = self.start + halfDiff
                            newEnd = self.end - halfDiff
                            self.cbShowAll.set(False)
                            self.cbUpdate.set(False)
                            self.start = newStart
                            self.end = newEnd
                            assert(self.end >= self.start)
                            self.displayedSeconds = self.end - self.start
                            self.scrollbar.setPageWidth(self.displayedSeconds)
                            self.scrollbar.setPos(self.start)
                    elif event.button == 5 and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        # zoom out
                        oldDuration = self.end - self.start
                        newDuration = oldDuration * 2.0
                        diff = newDuration - oldDuration
                        if diff < 60*60*24*365: # show at most one year
                            halfDiff = diff / 2.0
                            newStart = self.start - halfDiff
                            newEnd = self.end + halfDiff
                            self.cbShowAll.set(False)
                            self.cbUpdate.set(False)
                            self.start = newStart
                            self.end = newEnd
                            assert(self.end >= self.start)
                            self.displayedSeconds = newDuration
                            self.scrollbar.setPageWidth(self.displayedSeconds)
                            self.scrollbar.setPos(self.start)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.zooming:
                        self.zooming = False
                        pygame.mouse.set_cursor(*pygame.cursors.arrow)
                        if self.zoomStart[0] != self.zoomEnd[0]:
                            # calculate time from screen coordinate
                            x1 = self._xToPos(self.zoomStart[0])
                            x2 = self._xToPos(self.zoomEnd[0])
                            if x2 < x1:
                                (x2, x1) = (x1, x2)
                            self.cbShowAll.set(False)
                            self.cbUpdate.set(False)
                            self.start = x1
                            self.end = x2
                            self.displayedSeconds = self.end - self.start
                            self.scrollbar.setPageWidth( self.displayedSeconds )
                            self.scrollbar.setPos(self.start)

                    if self.panning:
                        self.panning = False
                        pygame.mouse.set_cursor(*pygame.cursors.arrow)
                elif event.type == pygame.MOUSEMOTION:
                    if self.zooming:
                        self.zoomEnd = event.pos
                    if self.panning:
                        diff = self._xToPos(self.panStartX) - self._xToPos(event.pos[0])
                        self.start = self.panStartTime + diff
                        self.end = self.start + self.displayedSeconds
                        self.scrollbar.setPos(self.start)
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

            if pygame.mouse.get_focused() and self.start is not None:
                pos = pygame.mouse.get_pos()
                t = self._xToPos(pos[0])
                timeStr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))
                fract = t - int(t)
                fractStr = "%f" % fract
                fractStr = fractStr[1:5]
                currentPos = "%s%s" % (timeStr, fractStr)
                self.lblCurrent.set(currentPos)
            else:
                self.lblCurrent.set("")

            self.screen.fill( (0, 0, 0) )

            nowTime = time.time()

            (availStart, availEnd) = self.store.getRange()
            if availStart is None:
                availStart = nowTime
            if availEnd is None:
                availEnd = nowTime

            if self.showAll:
                self.start = availStart
                self.end = availEnd
            elif self.update:
                self.end = nowTime
                self.start = self.end - self.displayedSeconds
                self.scrollbar.setPos(self.start)
            else:
                pass

            posEnd = max(availEnd, self.end, nowTime)
            self.scrollbar.setRange(availStart, posEnd)

#             (start, end) = self.store.getRange()
#             if start is None:
#                 start = time.time()
#                 end = time.time()
#             if (start - end) < 2.1:
#                 start = end - 2.1
            duration = self.end - self.start
            #print start, end

            allPoints = self.store.get(self.start, self.end)
            #print allPoints

            yMin = -10
            yMax = 110
            yRange = yMax - yMin

            factorY = float(self.height) / yRange


            # draw grid

            # show about 10 marks on X axis:
            xInterval = (duration * self.floatFactor) / 10.0
            xInterval = self._roundXInterval(xInterval)
            assert(int(xInterval) == xInterval)
            assert(xInterval > 0)
            xInterval = int(xInterval)
            # round grid start time to same interval:
            firstMark = int(self.start * self.floatFactor)
            firstMark = firstMark - (firstMark % xInterval)
            # TODO: the +2 offset is too little when zoomed out
            lastMark = int((self.end+2) * self.floatFactor)

            # show about 2-3 time labels on X axis:
            xTextInterval = (duration * self.floatFactor) / 2.5
            xTextInterval = self._roundXInterval(xTextInterval)
            assert(int(xTextInterval) == xTextInterval)
            assert(xTextInterval > 0)
            xTextInterval = int(xTextInterval)

            showDate = False
            startDate = datetime.datetime.fromtimestamp(self.start)
            endDate = datetime.datetime.fromtimestamp(self.end)
            if startDate.date() != endDate.date():
                showDate = True

            font = pygame.font.Font(None, 18)
            for tScaled in range(firstMark, lastMark, xInterval):
                t = float(tScaled) / self.floatFactor
                x = self._xToScreen(t)
                if x < -100 or x > self.width+100:
                    continue

                pygame.draw.line(self.screen, (64,64,64), (x,0), (x,self.height))

                if tScaled % (xTextInterval) == 0:
                    if showDate:
                        dateStr = time.strftime("%a, %Y-%m-%d", time.localtime(t))
                        surf = font.render(dateStr, True, (128,128,128))
                        self.screen.blit(surf, (x-(surf.get_width()/2), self.height-40))

                    timeStr = time.strftime("%H:%M:%S", time.localtime(t))
                    if tScaled % self.floatFactor != 0:
                        fract = int(tScaled % self.floatFactor)
                        formatString = "%0" + str(self.floatFactorLength) + "d"
                        fractStr = formatString % fract
                        fractStr = fractStr.rstrip('0')
                        timeStr += "." + fractStr
                    surf = font.render(timeStr, True, (128,128,128))
                    self.screen.blit(surf, (x-(surf.get_width()/2), self.height-20))

            for i in xrange(yMin, yMax, 10):
                y = self.height - ((i - yMin) * factorY)
                color = (64,64,64)
                if i % 100 == 0:
                    color = (128,128,128)
                pygame.draw.line(self.screen, color, (0,y), (self.width,y))


            for id,l in allPoints.items():
                #print len(l)
                if not(l):
                    continue
                if not(self.sourceLabels[id]['visible']):
                    continue
                if type(l[0][1]) == bool:
                    # event data
                    for e in l:
                        t = e[0]
                        value = e[1]
                        if value and t >= self.start and t <= self.end:
                            x = self._xToScreen(t)
                            pygame.draw.line(self.screen, (255,255,255), (x,0), (x,self.height))
                else:
                    # value data
                    points = []
                    for e in l:
                        t = e[0]
                        value = e[1]
                        x = self._xToScreen(t)
                        y = self.height - ((value - yMin) * factorY)
                        points.append( (x,y) )
                    if len(points) > 1:
                        pygame.draw.lines(self.screen, (255,255,255), False, points)

            self.lblDebug.set("%s - %s (%.3f) (%fs; %fs) (%.2f)" % (
                time.strftime("%c", time.localtime(self.start)), time.strftime("%c", time.localtime(self.end)),
                self.end-self.start,
                float(xInterval)/self.floatFactor, float(xTextInterval)/self.floatFactor,
                self.clock.get_fps()))

            for w in self.widgets:
                w.draw(self.screen)

            # draw zoom rectangle over everything else
            if self.zooming:
                rect = (self.zoomStart[0],
                        0,
                        self.zoomEnd[0] - self.zoomStart[0],
                        self.height
                        )
                pygame.draw.rect(self.screen, (255,255,128), rect, 1)

            #print self.clock.get_fps()
            pygame.display.flip()

