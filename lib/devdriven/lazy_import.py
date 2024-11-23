from typing import Any
import importlib

class Importer():
  def __init__(self, modname: str) -> None:
    self._modname = modname
    self._mod: Any = None

  def __getattr__(self, attr: str) -> Any:
    if self._mod is None:
      self._mod = importlib.import_module(self._modname)
    return getattr(self._mod, attr)

def load(modname: str) -> Importer:
  return Importer(modname)
