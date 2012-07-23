
import sys
import time
import datetime

from PyQt4 import QtGui
from PyQt4 import QtCore


#from PyQt4 import QtOpenGL

class Plotter(QtGui.QWidget):
#class Plotter(QtOpenGL.QGLWidget):
    def __init__ (self, parent, store = None):
        QtGui.QWidget.__init__(self, parent)
        #QtOpenGL.QGLWidget.__init__(self, parent)
        self.store = store

        self.visibleSeconds = 10
        self.start = None

    def _xToScreen (self, px):
        duration = self.end - self.start
        factorX = float(self.width()) / duration
        sx = (px - self.start) * factorX
        return sx

    def paintEvent (self, event):
        p = QtGui.QPainter(self)
        pen = QtGui.QPen(QtGui.QColor('black'))
        p.setPen(pen)

        nowTime = time.time()

        (availStart, availEnd) = self.store.getRange()
        if availStart is None:
            availStart = nowTime
        if availEnd is None:
            availEnd = nowTime

        if self.start is None:
            self.start = availStart
        self.end = self.start + self.visibleSeconds

        if self.end <= self.start:
            self.start-=1

        allPoints = self.store.get(self.start, self.end)

        yMin = -10
        yMax = 110
        yRange = yMax - yMin

        factorY = float(self.height()) / yRange


        # draw grid
        (firstMark, lastMark, xInterval, xTextInterval) = self.baseOutput.calcXMarkers(self.start, self.end)

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

            p.drawLine(x, 0, x, self.height())

            if tScaled % (xTextInterval) == 0:
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

        for i in xrange(yMin, yMax, 10):
            y = self.height() - ((i - yMin) * factorY)
            #color = SdlStyle.axisColors[1]
            #if i % 100 == 0:
            #    color = SdlStyle.axisColors[0]
            p.drawLine(0, y, self.width(), y)


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

