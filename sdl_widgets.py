
import pygame


class SdlWidget:
    def handleEvent (self, event):
        pass

    def draw (self, screen):
        pass



class SdlCheckbox:
    def __init__ (self, x, y, text, onChange=None):
        self.x = x
        self.y = y
        self.text = text
        self.onChange = onChange

        self.w = 16
        self.h = 16
        self._checked = False

    def set (self, checked):
        self._checked = checked

    def checked (self):
        return self._checked

    def handleEvent (self, e):
        if e.type == pygame.MOUSEBUTTONDOWN:
            #print "button down at %d/%d" % e.pos
            if e.pos[0] >= self.x and e.pos[0] <= self.x+self.w and \
               e.pos[1] >= self.y and e.pos[1] <= self.y+self.h:
                #print "  event is inside widget %s" % self
                self._checked = not(self._checked)
                if self.onChange:
                    self.onChange(self)

    def draw (self, screen):
        screen.fill( (0, 0, 0), (self.x, self.y, self.w, self.h) )

        points = []
        points.append( (self.x, self.y) )
        points.append( (self.x+self.w, self.y) )
        points.append( (self.x+self.w, self.y+self.h) )
        points.append( (self.x, self.y+self.h) )
        pygame.draw.lines(screen, (192,192,192), True, points)

        #font = pygame.font.get_default_font()
        font = pygame.font.Font(None, 20)
        surf = font.render(self.text, True, (192,192,192))
        screen.blit(surf, (self.x+self.w+5, self.y+1))

        if self._checked:
            points = []
            points.append( (self.x, self.y) )
            points.append( (self.x+self.w, self.y+self.h) )
            points.append( (self.x+self.w, self.y) )
            points.append( (self.x, self.y+self.h) )
            pygame.draw.lines(screen, (192,192,192), False, points)
