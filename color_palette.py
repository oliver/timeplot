
try:
    import hashlib
except ImportError:
    import md5 as hashlib

class ColorPalette:
    def getColor (self, plotId):
        h = hashlib.md5(str(plotId))

        return tuple([ ord(x) for x in h.digest()[:3] ])

