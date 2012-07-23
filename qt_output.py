
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
        
        self.currentRange = None
        self.store.registerUpdateHandler(self.onDataChanged)

        self.app = QtGui.QApplication(sys.argv)
        self.win = MainWindow()
        self.win.plotter.init(store)

        self.win.connect(self.win.actionZoomIn, QtCore.SIGNAL('activated()'), lambda: self.onZoom(2))
        self.win.connect(self.win.actionZoomOut, QtCore.SIGNAL('activated()'), lambda: self.onZoom(0.5))
        self.win.hscrollPlotter.connect(self.win.hscrollPlotter, QtCore.SIGNAL('valueChanged(int)'), lambda val: self.updateSlider())

    def onLoad (self):
        self.updateSlider()

    def onDataChanged (self, start, end):
        newRange = self.store.getRange()
        if newRange != self.currentRange:
            self.updateSlider()

    def onZoom (self, factor):
        self.win.plotter.visibleSeconds /= float(factor)
        self.updateSlider()
        self.win.plotter.update()

    def startTimer (self, usec, callback):
        timer = QtCore.QTimer()
        self.timers.append(timer)
        # TODO: handle return value of callback
        self.win.connect(timer, QtCore.SIGNAL('timeout()'), lambda: callback())
        timer.start(int(usec/1000.0))

    def updateSlider (self):
        (availStart, availEnd) = self.store.getRange()
        if availStart is None:
            return

        stayAtEnd = (self.win.hscrollPlotter.value() == self.win.hscrollPlotter.maximum())

        maxVal = (availEnd - self.win.plotter.visibleSeconds - availStart) * 1000
        self.win.hscrollPlotter.setRange(0, maxVal)

        self.win.hscrollPlotter.setPageStep(self.win.plotter.visibleSeconds * 1000)
        self.win.hscrollPlotter.setSingleStep(1000)

        if stayAtEnd:
            self.win.hscrollPlotter.setValue(self.win.hscrollPlotter.maximum())

        self.win.plotter.start = ((self.win.hscrollPlotter.value() / 1000.0) + availStart)
        self.win.plotter.update()

        self.currentRange = (availStart, availEnd)

    def run (self):
        # run onLoad method as soon as Qt mainloop has started
        QtCore.QTimer.singleShot(1, self.onLoad)

        self.win.show()
        self.app.exec_()

