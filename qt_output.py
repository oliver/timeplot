
import sys
import math
import time
from PyQt4 import QtGui
from PyQt4 import QtCore

#from config import Cfg
from base_output import *

from qt_output_ui import Ui_TimePlotWindow


class QScrollbarLong:
    "wrapper around QScrollbar, allowing to set a range > 2**32 (and also use float values)"
    INTERNAL_MAX = int(2**30)

    def __init__ (self, realScrollbar):
        assert isinstance(self.INTERNAL_MAX, int)
        
        self.realScrollbar = realScrollbar
        self.mini = None
        self.maxi = None
        self.pageStep = None

        self.internalRange = None
        self.internalPageStep = None

        self._lastValue = 0

    def _lengthToInternal (self, externalValue):
        externalLength = self.pageStep + self.maxi - self.mini
        internalLength = self.internalPageStep + self.internalRange

        factor = float(internalLength) / externalLength
        result = int(externalValue * factor)
        assert result <= self.INTERNAL_MAX, "internal value (%d) must be < max (%d); factor: %f" % (
            result, self.INTERNAL_MAX, factor)
        assert isinstance(result, int), "internal value (%d) is not an int; factor: %f" % (
            result, factor)
        return result

    def _lengthToExternal (self, externalValue):
        externalLength = self.pageStep + self.maxi - self.mini
        internalLength = self.internalPageStep + self.internalRange
        factor = float(internalLength) / externalLength
        return externalValue / factor

    def _posToInternal (self, externalPos):
        return self._lengthToInternal(externalPos - self.mini)

    def _posToExternal (self, internalPos):
        return self._lengthToExternal(internalPos) + self.mini


    def setRange (self, minimum, maximum, pageStep, singleStep):
        assert pageStep > 0
        assert singleStep > 0

        if self.mini != self.maxi:
            self._lastValue = self._posToExternal(self.realScrollbar.value())

        if maximum <= minimum:
            # special case: no scrolling possible
            self.mini = self.maxi = minimum
            self.realScrollbar.setRange(0, 0)
            self.realScrollbar.setPageStep(1)
            self.realScrollbar.setSingleStep(1)
            return

        self.mini = minimum
        self.maxi = maximum
        self.pageStep = pageStep

        length = pageStep + maximum - minimum
        assert length > 0
        assert length < self.INTERNAL_MAX, "really large ranges not supported yet"

        if pageStep > length:
            pageStep = length
        if singleStep > length:
            singleStep = length
            assert(False)

        assert pageStep <= length
        assert singleStep <= pageStep

        # use smaller (finer-grained) steps internally, to allow finer-grained scrollbar sliding:
        numMaxSteps = self.INTERNAL_MAX
        numNecessarySteps = math.ceil(float(length) / singleStep)

        if numNecessarySteps > numMaxSteps:
            assert False, "too many steps necessary (%f)" % numNecessarySteps
        else:
            stepFactor = int(numMaxSteps / numNecessarySteps)
            assert stepFactor >= 1
            numSteps = int(numNecessarySteps * stepFactor)

        assert numSteps <= numMaxSteps, "numSteps (%d) must be less or equal to numMaxSteps (%d); numNecessarySteps=%d, stepFactor=%d" % (
            numSteps, numMaxSteps, numNecessarySteps, stepFactor)
        assert numSteps >= numNecessarySteps

        
        internalPageStepFraction = pageStep / float(pageStep + maximum - minimum)
        assert internalPageStepFraction <= 1.0
        assert internalPageStepFraction > 0.0

        self.internalPageStep = numSteps * internalPageStepFraction
        self.internalRange = numSteps - self.internalPageStep

        self.realScrollbar.setRange(0, self.internalRange)
        self.realScrollbar.setPageStep( self._lengthToInternal(pageStep) )
        self.realScrollbar.setSingleStep( self._lengthToInternal(singleStep) )

        if self._lastValue is not None:
            self.setValue(self._lastValue)

    def setValue (self, value):
        if value < self.mini:
            value = self.mini
        elif value > self.maxi:
            value = self.maxi
        self._lastValue = value
        if not(self.mini == self.maxi):
            internalValue = self._posToInternal(value)
            self.realScrollbar.setValue(internalValue)

    def value (self):
        if self.mini == self.maxi:
            return self.mini
        else:
            return self._posToExternal(self.realScrollbar.value())

    def isAtMax (self):
        return (self.realScrollbar.value() == self.realScrollbar.maximum())


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

        self.hScroll = QScrollbarLong(self.win.hscrollPlotter)
        self.rangeLabel = QtGui.QLabel()
        self.win.statusBar().addWidget(self.rangeLabel)
        self.rangeLabel.show()
        positionLabel = QtGui.QLabel()
        self.win.statusBar().addWidget(positionLabel)
        positionLabel.show()

        self.win.plotter.init(store, positionLabel)

        self.win.connect(self.win.actionZoomIn, QtCore.SIGNAL('activated()'), lambda: self.onZoom(2))
        self.win.connect(self.win.actionZoomOut, QtCore.SIGNAL('activated()'), lambda: self.onZoom(0.5))
        self.win.hscrollPlotter.connect(self.win.hscrollPlotter, QtCore.SIGNAL('valueChanged(int)'), lambda val: self.sbHandleValueChanged())

    def onLoad (self):
        self.sbUpdateRange()

    def onDataChanged (self, start, end):
        newRange = self.store.getRange()
        if newRange != self.currentRange:
            self.sbUpdateRange()

    def onZoom (self, factor):
        self.win.plotter.visibleSeconds /= float(factor)
        self.sbUpdateRange()
        self.win.plotter.update()

    def startTimer (self, usec, callback):
        timer = QtCore.QTimer()
        self.timers.append(timer)
        # TODO: handle return value of callback
        self.win.connect(timer, QtCore.SIGNAL('timeout()'), lambda: callback())
        timer.start(int(usec/1000.0))

    def sbUpdateRange (self):
        "new range and/or pageSize for scrollbar (or onLoad event)"

        (availStart, availEnd) = self.store.getRange()
        if availStart is None:
            return

        stayAtEnd = self.hScroll.isAtMax()
        self.hScroll.setRange(math.floor(availStart), math.ceil(availEnd - self.win.plotter.visibleSeconds),
            self.win.plotter.visibleSeconds, self.win.plotter.visibleSeconds / 10.0)
        self.currentRange = (availStart, availEnd)

        if stayAtEnd:
            self.hScroll.setValue(math.ceil(availEnd - self.win.plotter.visibleSeconds))
            self.sbHandleValueChanged()

        self.updateRangeLabel()

    def sbHandleValueChanged (self):
        "value has been changed"
        self.win.plotter.start = self.hScroll.value()
        self.updateRangeLabel()
        self.win.plotter.update()


    def updateRangeLabel (self):
        if self.win.plotter.start is None:
            return

        startFloat = self.win.plotter.start
        endFloat = self.win.plotter.start + self.win.plotter.visibleSeconds

        startDate = QtCore.QDateTime.fromTime_t(int(startFloat))
        startFract = startFloat - int(startFloat)
        endDate  = QtCore.QDateTime.fromTime_t(int(endFloat))
        endFract = endFloat - int(endFloat)

        rangeText = u"displayed: %s%s - %s%s (%f s)" % (
            startDate.toString(QtCore.Qt.ISODate), ("%.06f" % startFract)[1:],
            endDate.toString(QtCore.Qt.ISODate), ("%.06f" % endFract)[1:],
            self.win.plotter.visibleSeconds)

        self.rangeLabel.setText(rangeText)


    def run (self):
        # run onLoad method as soon as Qt mainloop has started
        QtCore.QTimer.singleShot(1, self.onLoad)

        self.win.show()
        self.app.exec_()

