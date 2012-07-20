
import csv
import time
import dateutil.parser

from base_reader import InputReader
from event import EventMgr

class CsvReader (InputReader):
    def __init__ (self, sourceMgr, store, file):
        InputReader.__init__(self, store)
        self.filename = file
        self.ids = []
        self.timeParser = None

        self.fd = open(self.filename, 'rb')
        sampleText = self.fd.read(1024*20)
        dialect = csv.Sniffer().sniff(sampleText)
        self.fd.seek(0)

        self.reader = csv.reader(self.fd, dialect)
        if csv.Sniffer().has_header(sampleText):
            self.reader.next()

            # read header fields
            lines = sampleText.splitlines()[:2]
            dictReader = csv.DictReader(lines, dialect=dialect)
            dictReader.next()
            for name in dictReader.fieldnames[1:]:
                self.ids.append( sourceMgr.register('%s (%s)' % (name, self.filename)) )
            del dictReader
        else:
            self.ids.append( sourceMgr.register(self.filename) )

        self.readAvailableData()

        EventMgr.startTimer(100*1000, self.onTimer)

    def onTimer (self):
        offset = self.fd.tell()
        self.fd.seek(offset)
        self.readAvailableData()
        return True

    def readAvailableData (self):
        while True:
            try:
                r = self.reader.next()
            except StopIteration:
                break

            if self.timeParser is None:
                self.timeParser = self._detectTimeType(r[0])
            t = self.timeParser(r[0])

            i = 0
            for rawValue in r[1:]:
                v = float(rawValue)
                self.store.update( (self.ids[i], t, v) )
                i+=1


    def _parseTimeString (self, s):
        dt = dateutil.parser.parse(s, fuzzy=True)
        return time.mktime(dt.timetuple())

    def _detectTimeType (self, s):
        for parserFunc in [ float, self._parseTimeString ]:
            try:
                result = parserFunc(s)
            except:
                continue
            else:
                return parserFunc
        return None

