
class BaseOutput:
    def __init__ (self, model):
        self.model = model

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


    def startTimer (self, usec, callback):
        raise Exception("not implemented")

    def watchFd (self, fd, callback):
        raise Exception("not implemented")


    def onUpdate (self):
        pass

    def _roundXInterval (self, target):
        bestInterval = self._xIntervals[0]
        bestDiff = None
        for interval in self._xIntervals:
            diff = abs(target-interval)
            if bestDiff is None or diff < bestDiff:
                bestInterval = interval
                bestDiff = diff
        return bestInterval

    def calcXMarkers (self, start, end):
        """
        Calculates locations (as range and interval) for grid markers on X axis.
        start and end are time values (as float).
        
        Returns (firstMark, lastMark, xInterval, xTextInterval), which are
        scaled float values (based on self.floatFactor).
        """
        # show about 10 marks on X axis:
        duration = end - start
        xInterval = (duration * self.floatFactor) / 10.0
        xInterval = self._roundXInterval(xInterval)
        assert(int(xInterval) == xInterval)
        assert(xInterval > 0)
        xInterval = int(xInterval)
        # round grid start time to same interval:
        firstMark = int(start * self.floatFactor)
        firstMark = firstMark - (firstMark % xInterval)
        # TODO: the +2 offset is too little when zoomed out
        lastMark = int((end+2) * self.floatFactor)

        # show about 2-3 time labels on X axis:
        xTextInterval = (duration * self.floatFactor) / 2.5
        xTextInterval = self._roundXInterval(xTextInterval)
        assert(int(xTextInterval) == xTextInterval)
        assert(xTextInterval > 0)
        xTextInterval = int(xTextInterval)

        return (firstMark, lastMark, xInterval, xTextInterval)

