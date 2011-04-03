import os
import types
import imp

"""
Allows dynamic loading of classes by name.
"""

class ReaderLoader:
    def __init__ (self):
        self.classes = {}

        self.pathList = []
        self.pathList.append( os.path.dirname(os.path.realpath(__file__)) )

    def _updateModuleList (self):
        self.classes = {}

        modules = []
        for p in self.pathList:
            modules += self._listModules(p)
        for tup in modules:
            self._loadModule(tup[0], tup[1])

    def _listModules (self, path):
        modules = []
        for f in os.listdir(path):
            if f.endswith("_reader.py"):
                module = f[:-3]
                modules.append( (module, path) )
        return modules

    def _loadModule (self, moduleName, path):
        (fileName, modPath, desc) = imp.find_module(moduleName, [path])
        module = imp.load_module(moduleName, fileName, modPath, desc)

        for name, value in module.__dict__.items():
            if isinstance(value, types.ClassType):
                className = str(value).split('.')[-1]
                self.classes[className] = value

    def load (self, className):
        "returns the class object matching the requested name"

        self._updateModuleList()

        if self.classes.has_key(className):
            return self.classes[className]
        else:
            return None

