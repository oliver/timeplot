
class BaseOutput:
    def __init__ (self, model):
        self.model = model


    def startTimer (self, usec, callback):
        raise Exception("not implemented")

    def watchFd (self, fd, callback):
        raise Exception("not implemented")


    def onUpdate (self):
        pass

