
import sys
import time
import datetime
from PyQt4 import QtGui
from PyQt4 import QtCore

#from config import Cfg
from base_output import *


class Plotter(QtGui.QWidget):
    def __init__ (self, parent, store):
        QtGui.QWidget.__init__(self, parent)
        self.store = store

        self.showAll = False
        self.doUpdate = True
        self.displayedSeconds = 10

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

        if self.showAll:
            self.start = availStart
            self.end = availEnd
        elif self.doUpdate:
            self.end = nowTime
            self.start = self.end - self.displayedSeconds
            #self.scrollbar.setPos(self.start)
        else:
            pass

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


class QtOutput(BaseOutput):
    def __init__ (self, store, sourceMgr):
        BaseOutput.__init__(self, None)
        self.store = store
        self.sourceMgr = sourceMgr

        self.timers = []

        self.app = QtGui.QApplication(sys.argv)
        self.win = QtGui.QWidget()

    def startTimer (self, usec, callback):
        timer = QtCore.QTimer()
        self.timers.append(timer)
        # TODO: handle return value of callback
        self.win.connect(timer, QtCore.SIGNAL('timeout()'), lambda: callback())
        timer.start(int(usec/1000.0))

    def onRedraw (self):
        self.plotter.update()

    def run (self):
        self.win.resize(600, 400)
        self.win.setWindowTitle('Timeplot')
        vbox = QtGui.QVBoxLayout(self.win)

        self.plotter = Plotter(None, self.store)
        vbox.addWidget(self.plotter)

        redrawTimer = QtCore.QTimer()
        self.win.connect(redrawTimer, QtCore.SIGNAL('timeout()'), self.onRedraw)
        redrawTimer.start(30)

        self.win.show()
        self.app.exec_()

