
import sys
from PyQt4 import QtGui
from PyQt4 import QtCore

#from config import Cfg
from base_output import *

from qt_output_ui import Ui_TimePlotWindow


class MainWindow (QtGui.QMainWindow, Ui_TimePlotWindow):
    def __init__ (self):
        QtGui.QMainWindow.__init__(self)

        self.setupUi(self)


class QtOutput(BaseOutput):
    def __init__ (self, store, sourceMgr):
        BaseOutput.__init__(self, None)
        self.store = store
        self.sourceMgr = sourceMgr

        self.timers = []

        self.app = QtGui.QApplication(sys.argv)
        self.win = MainWindow()
        self.win.plotter.store = store

        self.win.connect(self.win.actionZoomIn, QtCore.SIGNAL('activated()'), lambda: self.onZoom(2))
        self.win.connect(self.win.actionZoomOut, QtCore.SIGNAL('activated()'), lambda: self.onZoom(0.5))

    def onZoom (self, factor):
        self.win.plotter.visibleSeconds /= factor

    def startTimer (self, usec, callback):
        timer = QtCore.QTimer()
        self.timers.append(timer)
        # TODO: handle return value of callback
        self.win.connect(timer, QtCore.SIGNAL('timeout()'), lambda: callback())
        timer.start(int(usec/1000.0))

    def onRedraw (self):
        self.win.plotter.update()

        (availStart, availEnd) = self.store.getRange()
        if availStart is not None:
            stayAtEnd = (self.win.hscrollPlotter.value() == self.win.hscrollPlotter.maximum())

            maxVal = (availEnd - self.win.plotter.visibleSeconds - availStart) * 1000
            self.win.hscrollPlotter.setRange(0, maxVal)

            self.win.hscrollPlotter.setPageStep(self.win.plotter.visibleSeconds * 1000)
            self.win.hscrollPlotter.setSingleStep(1000)

            if stayAtEnd:
                self.win.hscrollPlotter.setValue(self.win.hscrollPlotter.maximum())

            self.win.plotter.start = ((self.win.hscrollPlotter.value() / 1000.0) + availStart)

    def run (self):
        redrawTimer = QtCore.QTimer()
        self.win.connect(redrawTimer, QtCore.SIGNAL('timeout()'), self.onRedraw)
        redrawTimer.start(30)

        self.win.show()
        self.app.exec_()

