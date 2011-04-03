
"""
Primitive data binding to JSON, for loading and saving config data.

Example:
from config import Cfg
print Cfg.ui_settings.show_all # prints current value of this option
Cfg.ui_settings.show_all = True # automatically writes config to JSON file
"""

import json

_defaultSettings = """
{
    "_comment": "",

    "ui_settings":
    {
        "font_family": null,
        "show_all": false,
        "update": true,
        "x_min": null,
        "x_max": null
    },

    "settings":
    {
        "extend_path": []
    },

    "readers": []
}
"""


def MergeStructures (base, new):
    "Merges two data structures (containing nested dicts and lists)"

    if type(base) == dict:
        # dict contents are merged
        assert(type(new) == dict)
        for k in base:
            if new.has_key(k):
                if type(base[k]) != dict and type(base[k]) != list:
                    # primitive value
                    base[k] = new[k]
                else:
                    MergeStructures(base[k], new[k])
    elif type(base) == list:
        # list contents are simply appended
        base += new
    else:
        raise Exception("unexpected type")



class CfgProxyList:
    def __init__ (self, cfg, parent):
        self._cfg = cfg
        self._parent = parent

        assert(type(self._cfg) == list)

    def __getitem__ (self, index):
        assert(type(index) == int)
        subVal = self._cfg[index]
        if type(subVal) == dict:
            subObj = CfgProxyDict(subVal, self._parent)
        elif type(subVal) == list:
            subObj = CfgProxyList(subVal, self._parent)
        else:
            # primitive type
            subObj = subVal
        return subObj

    def append (self, obj):
        self._cfg.append(obj)
        self._parent.notifyChange()

    def notifyChange (self):
        self._parent.notifyChange()

    def copy (self):
        return self._cfg[:]


class CfgProxyDict:
    def __init__ (self, cfg, parent):
        self._cfg = cfg
        self._parent = parent

        assert(type(self._cfg) == dict)

    def __getattr__ (self, name):
        if self._cfg.has_key(name):
            subVal = self._cfg[name]
            if type(subVal) == dict:
                subObj = CfgProxyDict(subVal, self._parent)
            elif type(subVal) == list:
                subObj = CfgProxyList(subVal, self._parent)
            else:
                # primitive type
                subObj = subVal
            return subObj
        else:
            raise AttributeError()

    def __setattr__ (self, name, value):
        if name.startswith("_"):
            self.__dict__[name] = value
        else:
            self._cfg[name] = value
            self._parent.notifyChange()

    def notifyChange (self):
        self._parent.notifyChange()

    def copy (self):
        return self._cfg.copy()


class Config:
    def __init__ (self):
        self.path = None # TODO: set to per-user file path
        self.cfg = json.loads(_defaultSettings)

    def loadFile (self, path):
        fd = open(path, 'r')
        newCfg = json.load(fd)
        MergeStructures(self.cfg, newCfg)
        self.path = path

    def _write (self):
        if self.path:
            fd = open(self.path, 'w')
            json.dump(self.cfg, fd, indent=2)

    def notifyChange (self):
        self._write()

    def getRootDict (self):
        rootDict = CfgProxyDict(self.cfg, self)
        rootDict.__dict__['loadFile'] = lambda path: self.loadFile(path)
        return rootDict


config = Config()
Cfg = config.getRootDict()

