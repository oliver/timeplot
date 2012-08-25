
import sys
import time
import datetime

from base_output import BasePlotter

from PyQt4 import QtGui
from PyQt4 import QtCore


#from PyQt4 import QtOpenGL

def rangesOverlap (r1, r2):
    if r1[1] < r2[0] or r1[0] > r2[1]:
        return False
    return True


class Plotter(QtGui.QWidget, BasePlotter):
#class Plotter(QtOpenGL.QGLWidget):
    def __init__ (self, parent):
        QtGui.QWidget.__init__(self, parent)
        BasePlotter.__init__(self)
        #QtOpenGL.QGLWidget.__init__(self, parent)

        self.minStart = time.time()
        self.maxEnd = self.minStart + 1

        self.visibleSeconds = 10
        self.start = self.minStart
        self.end = self.start + self.visibleSeconds

        self._panning = False
        self._panStartX = None
        self._panStartTime = None

        self.setMouseTracking(True)

    def init (self, store, positionLabel):
        self.store = store
        self.positionLabel = positionLabel

        self.store.registerUpdateHandler(self.onDataChanged)

    def setMaxRange (self, start, end):
        "set maximum time range that can be displayed"
        self.minStart = start
        self.maxEnd = end

    def setDisplayedRange (self, start):
        self.start = start
        self.end = self.start + self.visibleSeconds

    def onDataChanged (self, dirtyStart, dirtyEnd):
        if self.start is None or rangesOverlap( (self.start, self.start+self.visibleSeconds), (dirtyStart, dirtyEnd) ):
            self.update()

    def _xToPos (self, sx):
        duration = self.end - self.start
        factorX = float(self.width()) / duration
        px = (sx / factorX) + self.start
        return px

    def _xToScreen (self, px):
        duration = self.end - self.start
        factorX = float(self.width()) / duration
        sx = (px - self.start) * factorX
        return sx

    def mouseMoveEvent (self, event):
        if self._panning:
            diff = self._xToPos(self._panStartX) - self._xToPos(event.x())
            newStart = self._panStartTime + diff
            newEnd = newStart + self.visibleSeconds

            if newEnd > self.maxEnd:
                newEnd = self.maxEnd
                newStart = newEnd - self.visibleSeconds
            if newStart < self.minStart:
                newStart = self.minStart
                newEnd = newStart + self.visibleSeconds

            if newStart != self.start or newEnd != self.end:
                self.start = newStart
                self.end = newEnd
                self.update()
                self.emit(QtCore.SIGNAL("startChanged()"))

        mouseSeconds = self._xToPos(event.x())
        mouseFract = mouseSeconds - int(mouseSeconds)
        mouseDate  = QtCore.QDateTime.fromTime_t(int(mouseSeconds))

        labelText = "mouse: %s%s" % (
            mouseDate.toString(QtCore.Qt.ISODate), ("%.06f" % mouseFract)[1:] )
        self.positionLabel.setText(labelText)

    def mousePressEvent (self, event):
        if not(self._panning) and (event.buttons() & QtCore.Qt.MidButton):
            self._panning = True
            self._panStartX = event.x()
            self._panStartTime = self.start

    def mouseReleaseEvent (self, event):
        if self._panning and not(event.buttons() & QtCore.Qt.MidButton):
            self._panning = False

    def wheelEvent (self, event):
        numDegrees = event.delta() / 8
        numSteps = numDegrees / 15.0 

        if (event.modifiers() & QtCore.Qt.ControlModifier):
            self.emit(QtCore.SIGNAL("zoomEvent(int)"), numSteps)
        elif (event.modifiers() & QtCore.Qt.ShiftModifier):
            self.emit(QtCore.SIGNAL("scrollPage(int)"), numSteps)
        else:
            self.emit(QtCore.SIGNAL("scrollStep(int)"), numSteps)

    def paintEvent (self, event):
        p = QtGui.QPainter(self)

        allPoints = self.store.get(self.start, self.end)

        yMin = -10
        yMax = 110
        yRange = yMax - yMin

        factorY = float(self.height()) / yRange


        # draw grid
        gridPen = QtGui.QPen(QtGui.QColor('silver'))
        gridPenStrong = QtGui.QPen(QtGui.QColor('grey'))
        p.setPen(gridPen)

        (firstMark, lastMark, xInterval, xTextInterval) = self.calcXMarkers(self.start, self.end)

        showDate = False
        startDate = datetime.datetime.fromtimestamp(self.start)
        endDate = datetime.datetime.fromtimestamp(self.end)
        if startDate.date() != endDate.date():
            showDate = True

        for tScaled in range(firstMark, lastMark, xInterval):
            t = float(tScaled) / self.floatFactor
            x = self._xToScreen(t)
            if x < -100 or x > self.width()+100:
                continue

            drawText = (tScaled % (xTextInterval) == 0)

            if drawText:
                p.setPen(gridPenStrong)

            p.drawLine(x, 0, x, self.height())

            if drawText:
                if showDate:
                    dateStr = time.strftime("%a, %Y-%m-%d", time.localtime(t))
                else:
                    dateStr = ''

                timeStr = time.strftime("%H:%M:%S", time.localtime(t))
                if tScaled % self.floatFactor != 0:
                    fract = int(tScaled % self.floatFactor)
                    formatString = "%0" + str(self.floatFactorLength) + "d"
                    fractStr = formatString % fract
                    fractStr = fractStr.rstrip('0')
                    timeStr += "." + fractStr

                timeStr += '\n' + dateStr
                p.drawText(x-200, self.height()-50, 400, 50, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom, timeStr)
                p.setPen(gridPen)

        for i in xrange(yMin, yMax, 10):
            y = self.height() - ((i - yMin) * factorY)
            drawStrongLine = (i % 100 == 0)
            if drawStrongLine:
                p.setPen(gridPenStrong)
            p.drawLine(0, y, self.width(), y)
            if drawStrongLine:
                p.setPen(gridPen)


        plotPen = QtGui.QPen(QtGui.QColor('black'))
        p.setPen(plotPen)

        for id,l in allPoints.items():
            if not(l):
                continue
            if type(l[0][1]) == bool:
                # event data
                pass
                for e in l:
                    t = e[0]
                    value = e[1]
                    if value and t >= self.start and t <= self.end:
                        x = self._xToScreen(t)
                        p.drawLine(x, 0, x, self.height())
            else:
                # value data
                points = []
                for e in l:
                    t = e[0]
                    value = e[1]
                    x = self._xToScreen(t)
                    y = self.height() - ((value - yMin) * factorY)
                    points.append( QtCore.QPoint(x,y) )
                if len(points) > 1:
                    poly = QtGui.QPolygon(points)
                    p.drawPolyline(poly)

