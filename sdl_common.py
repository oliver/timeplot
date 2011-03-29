
class SdlStyle:
    # dark style:
    bgColor = (0, 0, 0)
    fgColor = (192, 192, 192)
    fillColor = (128, 128, 128)
    interactColor = (255, 255, 0)

    axisColors = [
        (128, 128, 128),
        (64, 64, 64),
    ]


    def graphColor (id):
        import hashlib
        h = hashlib.md5(str(id))
        return tuple([ ord(x) for x in h.digest()[:3] ])

    graphColor = staticmethod(graphColor)
