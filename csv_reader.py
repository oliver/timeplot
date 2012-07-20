
import csv

from base_reader import InputReader
from event import EventMgr

class CsvReader (InputReader):
    def __init__ (self, sourceMgr, store, file):
        InputReader.__init__(self, store)
        self.filename = file
        self.ids = []

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
            t = float(r[0])

            i = 0
            for rawValue in r[1:]:
                v = float(rawValue)
                self.store.update( (self.ids[i], t, v) )
                i+=1
