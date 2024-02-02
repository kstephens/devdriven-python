from typing import Any, Optional, Callable
from dataclasses import dataclass, field
import logging
import os
import pickle
# from icecream import ic

@dataclass
class PickleCache():
  path: str
  generate: Optional[Callable] = field(default=None)
  _data: Any = field(default=None)
  _ready: bool = field(default=False)
  _stale: bool = field(default=False)

  def exists(self):
    return os.path.isfile(self.path)

  def is_ready(self) -> bool:
    return self._ready

  def write(self):
    logging.debug('%s', f'write : {self.path!r}')
    assert self._ready
    with open(self.path, 'wb') as io:
      pickle.dump(self._data, io)
      self._stale = False

  def read(self):
    logging.debug('%s', f'read : {self.path!r}')
    with open(self.path, 'rb') as io:
      self._data = pickle.load(io)
      self._ready = True

  def set_data(self, data: Any):
    logging.debug('%s', f'set_data : {self.path!r}')
    self._data = data
    self._ready = True
    self._stale = True
    self.write()

  def data(self) -> Any:
    logging.debug('%s', f'data : {self.path!r}')
    if not self._ready:
      if self.exists():
        self.read()
      else:
        assert self.generate
        self.set_data(self.generate())
    assert self._ready
    return self._data
