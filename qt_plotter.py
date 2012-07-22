
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

