import importlib

def load(modname):
  return Importer(modname)

class Importer():
  def __init__(self, modname):
    self._modname  = modname
    self._mod = None

  def __getattr__(self, attr):
    if self._mod is None:
      self._mod = importlib.import_module(self._modname)
    return getattr(self._mod, attr)
