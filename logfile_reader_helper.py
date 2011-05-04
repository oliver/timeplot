
import time
import re

from base_reader import InputReader

class LogfileReader (InputReader):
    def __init__ (self, sourceMgr, store, logParser, matches):
        InputReader.__init__(self, store)
        self.matchers = []

        for m in matches:
            expr = m['expr']
            id = sourceMgr.register(expr)
            self.matchers.append( (id, expr) )

        now = time.time()
        for line in logParser.lines(None, now):
            self._handleLine(line)

    def _handleLine (self, line):
        (timestamp, msg) = line
        for m in self.matchers:
            result = re.search(m[1], msg)
            if result:
                if result.groups():
                    # RegExp has bracketed parts
                    value = float( result.group(1) )
                else:
                    value = True
                self.store.update( (m[0], timestamp, value) )
