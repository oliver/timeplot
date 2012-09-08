
try:
    import hashlib
except ImportError:
    import md5 as hashlib
import colorsys

class ColorPalette:
    def __init__ (self):
        self._hsvHueWalker_gen = self._hsvHueWalker()
        self._hsvFullWalker_gen = self._hsvFullWalker()

    def getColor (self, plotId):
        #return self._getHashColor(plotId)
        #return self._getHashHSVColor(plotId)
        #return self._getHueVariationColor(plotId)
        return self._hsvToRgb(self._hsvHueWalker_gen.next())
        #return self._hsvToRgb(self._hsvFullWalker_gen.next())


    def _hsvToRgb (self, hsvFractTuple):
        rgb = colorsys.hsv_to_rgb(*hsvFractTuple)
        rgb = [int(x*255.0) for x in rgb]
        return tuple(rgb)


    def _getHashColor (self, plotId):
        "use first bytes of MD5 hash of plotId as RGB values"
        h = hashlib.md5(str(plotId)*10)
        return tuple([ ord(x) for x in h.digest()[:3] ])


    def _getHashHSVColor (self, plotId):
        "use first bytes of MD5 hash of plotId as HSV values, then adjust HSV values for nicer colors"
        h = hashlib.md5(str(plotId)*10)
        hsv = [ ord(x)/255.0 for x in h.digest()[:3] ]
        hsv[1] = 0.7
        hsv[2] /= 2
        hsv[2] += 0.5
        return self._hsvToRgb(hsv)


    def _getHueVariationColor (self, plotId):
        "use plotId as index for hue value (S and V are static)"
        hsv = [None, 1, 0.75]

        def indexToValue (index, numAvailParts):
            """
            Converts an index (>= 0) into a value between 0.0 and 1.0.
            Higher index values lead to increasingly finer granulation of the value range.
            """
            while True:
                if index < numAvailParts:
                    break
                index -= numAvailParts
                numAvailParts *= 2
            value = (1.0 / numAvailParts) * (index+1)
            value -= (0.5 / numAvailParts)
            assert(value >= 0.0)
            assert(value < 1.0)
            return value

        hsv[0] = indexToValue(plotId, 3)
        return self._hsvToRgb(hsv)


    def _hsvHueWalker (self):
        """
        Generator function for jumping through HSV space:
        - use increasingly finer-granulated hues
        """

        hueParts = 3
        while True:
            sat = 1
            val = 0.75
            for hueIndex in range(hueParts):
                hue = (1.0 / hueParts) * (hueIndex+1)
                hue -= (0.5 / hueParts)

                hue -= (1.0/6)
                if hue < 0: hue += 1

                assert(hue >= 0)
                assert(hue < 1)
                yield (hue, sat, val)
            hueParts *= 2

    def _hsvFullWalker (self):
        """
        Generator function for more complicated jumps through HSV space:
        - use increasingly finer-granulated hues
        - modify S and V values to create different colors from the same hue value
        """

        hueParts = 3
        while True:
            for (sat, val) in [(1, 0.8), (0.5, 0.6)]:
                for hueIndex in range(hueParts):
                    hue = (1.0 / hueParts) * (hueIndex+1)
                    hue -= (0.5 / hueParts)

                    hue -= (1.0/6)
                    if hue < 0: hue += 1

                    assert(hue >= 0)
                    assert(hue < 1)
                    yield (hue, sat, val)

            hueParts *= 2

