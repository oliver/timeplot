
import csv

from timeplot import InputReader

class CsvReader (InputReader):
    def __init__ (self, store, filename):
        InputReader.__init__(self, store)
        self.filename = filename

    def start (self):
        fd = open(self.filename, 'rb')
        sampleText = fd.read(1024)
        dialect = csv.Sniffer().sniff(sampleText)
        fd.seek(0)

        reader = csv.reader(fd, dialect)
        if csv.Sniffer().has_header(sampleText):
            reader.next()

        for r in reader:
            t = float(r[0])
            v = float(r[1])
            self.store.update( (self.id, t, v) )
