print(__file__); print(__name__)

from .base import Base, register
from pathlib import Path

class Paths():
  def __init__(self, paths):
    self.paths = map(Path, paths)
  def __repr__(self):
    return f'Paths({self.paths!r})'
class In(Base):
  def xform(self, inp):
    if not self.args:
      self.args.append('-')
    return Paths(self.args)
register(In, 'in')

class Out(Base):
  def xform(self, inp):
    inp = str(inp)
    if not self.args:
      self.args.append('-')
    for arg in self.args:
      self.write_file(arg, inp)
    return None
register(Out, 'out')

class NullXform(Base):
  def xform(self, inp):
    return inp
register(NullXform, 'null')
