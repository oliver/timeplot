
#
# Provides a global object (EventMgr) for accessing the global event loop.
#

class _EventClass:
    def setImpl (self, impl):
        self.impl = impl

    def startTimer (self, usec, callback):
        """
        Sets up a timer which calls callback in specified interval.
        If callback returns False, timer will be stopped.
        """
        return self.impl.startTimer(usec, callback)

    def watchFd (self, fd, callback):
        return self.impl.watchFd(fd, callback)

EventMgr = _EventClass()
