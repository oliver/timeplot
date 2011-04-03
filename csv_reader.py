
import csv

from base_reader import InputReader
from event import EventMgr

class CsvReader (InputReader):
    def __init__ (self, sourceMgr, store, file):
        InputReader.__init__(self, store)
        self.filename = file

        self.fd = open(self.filename, 'rb')
        sampleText = self.fd.read(1024)
        dialect = csv.Sniffer().sniff(sampleText)
        self.fd.seek(0)

        self.reader = csv.reader(self.fd, dialect)
        if csv.Sniffer().has_header(sampleText):
            self.reader.next()

            # read header fields
            lines = sampleText.splitlines()[:2]
            dictReader = csv.DictReader(lines, dialect=dialect)
            self.id = sourceMgr.register('%s (%s)' % (dictReader.fieldnames[1], self.filename))
            del dictReader
        else:
            self.id = sourceMgr.register(self.filename)

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
            v = float(r[1])
            self.store.update( (self.id, t, v) )
