
import csv
import time
import dateutil.parser

from base_reader import InputReader
from event import EventMgr

class CsvReader (InputReader):
    def __init__ (self, sourceMgr, store, file):
        InputReader.__init__(self, store)
        self.filename = file
        self.lineNo = 0
        self.ids = []
        self.timeParser = None
        self.columnParsers = []

        self.fd = open(self.filename, 'rb')
        sampleText = self.fd.read(1024*20)
        dialect = csv.Sniffer().sniff(sampleText)
        self.fd.seek(0)

        self.reader = csv.reader(self.fd, dialect)
        if csv.Sniffer().has_header(sampleText):
            self.reader.next()
            self.lineNo+=1

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
            self.lineNo+=1

            if self.timeParser is None:
                self.timeParser = self._detectTimeType(r[0])
            t = self.timeParser(r[0])

            i = 0
            for rawValue in r[1:]:
                if len(self.columnParsers) <= i:
                    # initialize list of possible parsers for this column:
                    self.columnParsers.append( [float, self._parseFloatComma] )

                # try all available parser functions, and remove those that fail:
                parsers = self.columnParsers[i][:]
                assert(len(parsers) > 0)
                for parser in parsers:
                    try:
                        v = parser(rawValue)
                    except Exception, e:
                        if len(self.columnParsers[i]) <= 1:
                            raise Exception("failed to parse CSV value '%s' (line %d, table column %d) as '%s': %s" % (
                                rawValue, self.lineNo, i+2, parser, e) )
                        else:
                            self.columnParsers[i].remove(parser)
                    else:
                        break

                self.store.update( (self.ids[i], t, v) )
                i+=1


    # time parsing
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


    # value parsing
    def _parseFloatComma (self, s):
        "parse float value with comma instead of dot"
        return float(s.replace(',', '.'))

