
import time

from logfile_reader_helper import LogfileReader


class SyslogParser:
    def __init__ (self):

        self._lines = []
        self.fd = open('/var/log/syslog', 'r')
        for line in self.fd:
            (t, hostname, msg) = self._parseLine(line)
            self._lines.append( (t, hostname, msg) )
        print "parsed %d lines" % len(self._lines)

    def _parseLine (self, line):
        line = line.rstrip('\n')

        dateStr = line[:15]
        timeTup = time.strptime(dateStr, '%b %d %H:%M:%S')
        timeList = list(timeTup)
        timeList[0] = time.localtime()[0]
        timeTup = tuple(timeList)
        timestamp = time.mktime(timeTup)

        (hostname, msg) = line[16:].split(None, 1)
        #print "'%s'; '%f', '%s'; '%s'" % (dateStr, timestamp, hostname, msg)
        return (timestamp, hostname, msg)

    def lines (self, start, end):
        for tup in self._lines:
            if (tup[0] is None or tup[0] >= start) and (end is None or tup[0] <= end):
                yield (tup[0], tup[-1])


class SyslogReader (LogfileReader):
    def __init__ (self, sourceMgr, store, matches={}):
        parser = SyslogParser()
        LogfileReader.__init__(self, sourceMgr, store, parser, matches)
