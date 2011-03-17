
import csv

from timeplot import InputReader
from event import EventMgr

class CsvReader (InputReader):
    def __init__ (self, store, filename):
        InputReader.__init__(self, store)
        self.filename = filename

    def start (self):
        self.fd = open(self.filename, 'rb')
        sampleText = self.fd.read(1024)
        dialect = csv.Sniffer().sniff(sampleText)
        self.fd.seek(0)

        self.reader = csv.reader(self.fd, dialect)
        if csv.Sniffer().has_header(sampleText):
            self.reader.next()

        self.readAvailableData()

        EventMgr.startTimer(100*1000, self.readAvailableData)

    def readAvailableData (self):
        offset = self.fd.tell()
        self.fd.seek(offset)
        while True:
            try:
                r = self.reader.next()
            except StopIteration:
                break
            t = float(r[0])
            v = float(r[1])
            self.store.update( (self.id, t, v) )
        return True
