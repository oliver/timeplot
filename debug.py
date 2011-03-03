
# import ipdb
# class _IpythonDebugger:
#     def brk (self):
#         try:
#             ipdb.set_trace()
#         except KeyboardInterrupt:
#             #print "KeyboardInterrupt..."
#             pass
#         except:
#             pass



# class _IpythonDebugger:
#     def brk (self):
#         import sys

#         #print sys.path
#         ipythonPath = '/work/og/inst/ipython-0.9.1/'
#         if not(ipythonPath in sys.path):
#             sys.path.append(ipythonPath)

#         from IPython.ipapi import make_session
#         make_session()
#         from IPython.Debugger import Pdb
#         Pdb().set_trace()


class _PdbDebugger:
    def brk (self):
        import pdb
        try:
            pdb.set_trace()
        except:
            pass

DBG = _PdbDebugger()
