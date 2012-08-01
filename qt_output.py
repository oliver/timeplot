
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

    def _lengthToInternal (self, externalValue):
        externalLength = self.pageStep + self.maxi - self.mini
        internalLength = self.internalPageStep + self.internalRange

        factor = float(internalLength) / externalLength
        result = int(round(externalValue * factor))
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

        if maximum <= minimum:
            # special case: no scrolling possible
            self.mini = self.maxi = minimum
            self.realScrollbar.setRange(0, 0)
            self.realScrollbar.setPageStep(1)
            self.realScrollbar.setSingleStep(1)
            return

        oldValue = None
        if self.mini != self.maxi:
            oldValue = self._posToExternal(self.realScrollbar.value())

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

        # Ideally, the internal scrollbar should be split into enough separate "steps"
        # to represent the following three values without loss of precision:
        # - singleStep size
        # - current value set in the scrollbar (here: oldValue)
        # - external scrollbar length
        # So we need the greatest common divisor of these three values.

        def greatestCommonDivisor (a, b):
            while b:
                (a, b) = (b, a % b)
            return a

        necessaryStepFactor1 = singleStep
        necessaryStepFactor2 = greatestCommonDivisor(length, singleStep)
        if oldValue is not None:
            necessaryStepFactor3 = greatestCommonDivisor((oldValue - self.mini), necessaryStepFactor2)
        else:
            necessaryStepFactor3 = necessaryStepFactor2

        # it's not always possible to satisfy all three conditions listed above;
        # so this is an ordered list of "necessaryStepFactor" values (best factor first) which will be tried:
        necessaryStepFactors = [necessaryStepFactor3, necessaryStepFactor2, necessaryStepFactor1]

        # add some more "fallback" step factors which are somewhat compatible with the best ones:
        for i in range(20):
            necessaryStepFactors.append( necessaryStepFactors[-1] * 2.0 )

        # try all step factors until one fits:
        # (using suboptimal factors might lead to rounding problems the scrollbar value)
        numMaxSteps = self.INTERNAL_MAX
        for necessaryStepFactor in necessaryStepFactors:
            numNecessarySteps = math.ceil(float(length) / necessaryStepFactor)
            if numNecessarySteps <= numMaxSteps:
                break

        if numNecessarySteps > numMaxSteps:
            #print "still too many steps necessary (%f); reducing to %d" % (numNecessarySteps, numMaxSteps)
            numNecessarySteps = numMaxSteps
            numSteps = numMaxSteps
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

        if oldValue is not None:
            self.setValue(oldValue)

    def setValue (self, value):
        if value < self.mini:
            value = self.mini
        elif value > self.maxi:
            value = self.maxi
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

