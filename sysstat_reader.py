
#
# Reader for "Sysstat" values
#
# Currently only reads CPU load values, and only at startup, and only for the current day.
#

import time
import subprocess

from base_reader import InputReader

class SysstatReader (InputReader):
    def __init__ (self, sourceMgr, store):
        InputReader.__init__(self, store)

        cmd = ['sadf']
        output = subprocess.Popen(cmd, stdout=subprocess.PIPE, env={}).communicate()[0]

        fields = {}
        for line in output.splitlines():
            (host, interval, timestamp, dev, name, rawValue) = line.split()
            fullName = '%s-%s' % (dev, name)
            if not(fields.has_key(fullName)):
                id = sourceMgr.register("sysstat (%s)" % fullName)
                fields[fullName] = id
            else:
                id = fields[fullName]

            t = int(timestamp)
            value = float(rawValue)

            self.store.update( (id, t, value) )
