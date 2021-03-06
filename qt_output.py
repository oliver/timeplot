
import sys
import math
import time
from PyQt4 import QtGui
from PyQt4 import QtCore

#from config import Cfg
from base_output import *
from color_palette import *

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

        self.winSettings = QtCore.QSettings("timeplot", "timeplot")

        self.setupUi(self)

        self.restoreGeometry(self.winSettings.value("mainwin/geometry").toByteArray())
        self.restoreState(self.winSettings.value("mainwin/state").toByteArray())

    def closeEvent (self, event):
        self.winSettings.setValue("mainwin/geometry", QtCore.QVariant(self.saveGeometry()))
        self.winSettings.setValue("mainwin/state", QtCore.QVariant(self.saveState()))

        QtGui.QMainWindow.closeEvent(self, event)


class QtOutput(BaseOutput):
    def __init__ (self, store, sourceMgr):
        BaseOutput.__init__(self, None)
        self.store = store
        self.sourceMgr = sourceMgr

        self.timers = []

        self.colors = ColorPalette()
        
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

        self.listModel = QtGui.QStandardItemModel()
        self.win.lstSources.setModel(self.listModel)

        self.win.plotter.init(store, positionLabel)

        self.win.connect(self.win.actionZoomIn, QtCore.SIGNAL('activated()'), lambda: self.onZoom(2))
        self.win.connect(self.win.actionZoomOut, QtCore.SIGNAL('activated()'), lambda: self.onZoom(0.5))
        self.win.hscrollPlotter.connect(self.win.hscrollPlotter, QtCore.SIGNAL('valueChanged(int)'), lambda val: self.sbHandleValueChanged())
        self.win.plotter.connect(self.win.plotter, QtCore.SIGNAL('startChanged()'), lambda: self.handlePlotterChanged())
        self.win.plotter.connect(self.win.plotter, QtCore.SIGNAL('scrollStep(int)'), lambda numSteps: self.handlePlotterScrollStep(numSteps))
        self.win.plotter.connect(self.win.plotter, QtCore.SIGNAL('scrollPage(int)'), lambda numSteps: self.handlePlotterScrollPage(numSteps))
        self.win.plotter.connect(self.win.plotter, QtCore.SIGNAL('zoomEvent(int,double)'), lambda numSteps, centerTime: self.onZoom(2 ** numSteps, centerTime))
        self.win.connect(self.listModel, QtCore.SIGNAL('itemChanged(QStandardItem*)'), lambda item: self.listItemChanged(item))

    def onLoad (self):
        self.sbUpdateRange()

        for (id, sourceName) in self.sourceMgr.sources():
            item = QtGui.QStandardItem(sourceName)
            item.setData(QtCore.QVariant(id), QtCore.Qt.UserRole)
            plotColor = self.colors.getColor(id)
            item.setData( QtCore.QVariant(QtGui.QColor(*plotColor)) , QtCore.Qt.DecorationRole)
            item.setCheckState(QtCore.Qt.Checked)
            item.setCheckable(True)
            item.setEditable(False)
            self.listModel.appendRow(item)
            self.win.plotter.setVisibility(id, True)
            self.win.plotter.setColor(id, plotColor)

    def listItemChanged (self, item):
        plotId = item.data(QtCore.Qt.UserRole).toPyObject()
        self.win.plotter.setVisibility(plotId, item.checkState() == QtCore.Qt.Checked)
        self.win.plotter.update()

    def onDataChanged (self, start, end):
        newRange = self.store.getRange()
        if newRange != self.currentRange:
            self.sbUpdateRange()

    def onZoom (self, factor, centerTime = None):
        if centerTime is None:
            centerTime = self.hScroll.value() + (self.win.plotter.visibleSeconds / 2.0)

        diffOld = centerTime - self.hScroll.value()
        diffNew = diffOld / float(factor)
        newStart = centerTime - diffNew

        self.win.plotter.visibleSeconds /= float(factor)
        
        (availStart, availEnd) = self.store.getRange()
        if newStart + self.win.plotter.visibleSeconds > availEnd:
            newStart = availEnd - self.win.plotter.visibleSeconds
        if newStart < availStart:
            newStart = availStart

        self.sbUpdateRange()
        self.hScroll.setValue(newStart)
        self.win.plotter.setDisplayedRange(newStart)
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

        minStart = math.floor(availStart)
        maxEnd = math.ceil(availEnd - self.win.plotter.visibleSeconds)
        self.win.plotter.setMaxRange(minStart, maxEnd + self.win.plotter.visibleSeconds)

        stayAtEnd = self.hScroll.isAtMax()
        self.hScroll.setRange(minStart, maxEnd,
            self.win.plotter.visibleSeconds, self.win.plotter.visibleSeconds / 10.0)
        self.currentRange = (availStart, availEnd)

        if stayAtEnd:
            self.hScroll.setValue(math.ceil(availEnd - self.win.plotter.visibleSeconds))
            self.sbHandleValueChanged()

        self.updateRangeLabel()

    def sbHandleValueChanged (self):
        "value has been changed"
        self.win.plotter.setDisplayedRange(self.hScroll.value())
        self.updateRangeLabel()
        self.win.plotter.update()

    def handlePlotterChanged (self):
        self.hScroll.setValue(self.win.plotter.start)
        self.updateRangeLabel()

    def handlePlotterScrollStep (self, numSteps):
        self.hScroll.setValue( self.hScroll.value() + ((self.win.plotter.visibleSeconds / 10.0) * numSteps * -1 * 3.0) )

    def handlePlotterScrollPage (self, numSteps):
        self.hScroll.setValue( self.hScroll.value() + (self.win.plotter.visibleSeconds * numSteps * -1) )

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

