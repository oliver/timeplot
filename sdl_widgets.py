
import pygame
from sdl_common import *


class SdlWidget:
    def __init__ (self):
        self.visible = True

    def handleEvent (self, event):
        pass

    def draw (self, screen):
        pass

    def setVisibility (self, visible):
        self.visible = visible


class SdlHScrollbar (SdlWidget):
    def __init__ (self, x, y, w, h, pageWidth, lineScroll, onChange=None):
        SdlWidget.__init__(self)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.pwidth = pageWidth
        self.lineScroll = lineScroll
        self.onChange = onChange

        self.start = 0
        self.end = 1
        self.pos = self.start

        self.dragging = False
        self.offsetX = None

    def setRange (self, start, end):
        self.start = start
        self.end = end

    def setPageWidth (self, pageWidth):
        self.pwidth = pageWidth

    def setPos (self, pos):
        self.pos = pos

    def getPos (self):
        return self.pos


    def _getThumb (self):
        if self.end <= self.start:
            return (0, self.w)
        pixPerUnit = self.w / (self.end - self.start)
        thumbWidth = self.pwidth * pixPerUnit
        thumbWidth = min(thumbWidth, self.w)
        thumbX = (self.pos - self.start) * pixPerUnit
        thumbX = max(0, thumbX)
        if thumbWidth < 10:
            thumbWidth = 10
            if self.w + thumbWidth > thumbX:
                thumbX = min(thumbX, self.w - thumbWidth)
        return (thumbX, thumbWidth)

    def _calcPos (self, mouseX):
        if (self.end - self.start) < self.pwidth:
            return
        newPos = (float(mouseX - self.x) / self.w) * (self.end - self.start)
        newPos += self.start
        self._updatePos(newPos)

    def _updatePos (self, newPos):
        newPos = min(newPos, self.end-self.pwidth)
        newPos = max(newPos, self.start)
        self.pos = newPos
        if self.onChange:
            self.onChange(self)

    def handleEvent (self, e):
        if not(self.visible): return

        if e.type == pygame.MOUSEBUTTONDOWN:
            #print "button down at %d/%d" % e.pos
            if e.pos[0] >= self.x and e.pos[0] <= self.x+self.w and \
               e.pos[1] >= self.y and e.pos[1] <= self.y+self.h:
                #print "  event is inside widget %s" % self

                if e.button == 1:
                    (thumbX, thumbWidth) = self._getThumb()
                    if e.pos[0] < self.x + thumbX:
                        self._updatePos(self.pos - self.pwidth)
                    elif e.pos[0] > self.x + thumbX + thumbWidth:
                        self._updatePos(self.pos + self.pwidth)
                    else:
                        self.dragging = True
                        self.offsetX = e.pos[0] - (self.x + thumbX)
                elif e.button == 2:
                    # middle click goes directly to selected position
                    self._calcPos(e.pos[0])
                elif e.button == 4:
                    # wheel up
                    self._updatePos(self.pos - self.lineScroll)
                elif e.button == 5:
                    # wheel down
                    self._updatePos(self.pos + self.lineScroll)
                return True
        elif e.type == pygame.MOUSEBUTTONUP:
            if self.dragging:
                self.dragging = False
                return True
        elif e.type == pygame.MOUSEMOTION:
            if self.dragging:
                self._calcPos(e.pos[0] - self.offsetX)
                return True


    def draw (self, screen):
        if not(self.visible): return

        screen.fill( SdlStyle.bgColor, (self.x, self.y, self.w, self.h) )

        (thumbX, thumbWidth) = self._getThumb()
        screen.fill( SdlStyle.fillColor, (self.x+thumbX, self.y, thumbWidth, self.h) )

        points = []
        points.append( (self.x, self.y) )
        points.append( (self.x+self.w, self.y) )
        points.append( (self.x+self.w, self.y+self.h) )
        points.append( (self.x, self.y+self.h) )
        pygame.draw.lines(screen, SdlStyle.fgColor, True, points)



class SdlCheckbox (SdlWidget):
    def __init__ (self, x, y, text, onChange=None):
        SdlWidget.__init__(self)
        self.x = x
        self.y = y
        self.onChange = onChange

        self.w = 16
        self.h = 16
        self._checked = False

        font = pygame.font.Font(None, 20)
        self.textSurface = font.render(text, True, SdlStyle.fgColor)
        self.fullW = self.w + self.textSurface.get_width() + 5 + 5

    def set (self, checked):
        self._checked = checked
        if self.onChange:
            self.onChange(self)

    def checked (self):
        return self._checked

    def handleEvent (self, e):
        if not(self.visible): return

        if e.type == pygame.MOUSEBUTTONDOWN:
            #print "button down at %d/%d" % e.pos
            if e.pos[0] >= self.x and e.pos[0] <= self.x+self.fullW and \
               e.pos[1] >= self.y and e.pos[1] <= self.y+self.h:
                #print "  event is inside widget %s" % self
                self._checked = not(self._checked)
                if self.onChange:
                    self.onChange(self)
                return True

    def draw (self, screen):
        if not(self.visible): return

        screen.fill( SdlStyle.bgColor, (self.x, self.y, self.w, self.h) )

        points = []
        points.append( (self.x, self.y) )
        points.append( (self.x+self.w, self.y) )
        points.append( (self.x+self.w, self.y+self.h) )
        points.append( (self.x, self.y+self.h) )
        pygame.draw.lines(screen, SdlStyle.fgColor, True, points)

        screen.blit(self.textSurface, (self.x+self.w+5, self.y+1))

        if self._checked:
            points = []
            points.append( (self.x, self.y) )
            points.append( (self.x+self.w, self.y+self.h) )
            points.append( (self.x+self.w, self.y) )
            points.append( (self.x, self.y+self.h) )
            pygame.draw.lines(screen, SdlStyle.fgColor, False, points)



class SdlLabel (SdlWidget):
    def __init__ (self, x, y, color=SdlStyle.fgColor):
        SdlWidget.__init__(self)
        self.x = x
        self.y = y
        self.color = color

        self.font = pygame.font.Font(None, 20)
        self.textSurface = self.font.render("", True, self.color)

    def set (self, text):
        self.textSurface = self.font.render(text, True, self.color)

    def draw (self, screen):
        if not(self.visible): return

        screen.blit(self.textSurface, (self.x, self.y))
