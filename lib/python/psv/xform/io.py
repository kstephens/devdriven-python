print(__file__); print(__name__)

from .base import Base, register
from pathlib import Path
import sys

class Paths():
  def __init__(self, paths):
    self.paths = list(map(Path, paths))
  def __repr__(self):
    return f'Paths({self.paths!r})'
  def to_dict(self):
    return ['Paths:', list(map(str, self.paths))]
  def __str__(self):
    return ''.join(map(read_file, self.paths))

class In(Base):
  def xform(self, inp):
    if not self.args:
      self.args.append('-')
    return Paths(self.args)
register(In, 'in')

class Out(Base):
  def xform(self, inp):
    ic(inp)
    inp = str(inp)
    if not self.args:
      self.args.append('-')
    for arg in self.args:
      write_file(arg, inp)
    return None
register(Out, 'out')

class NullXform(Base):
  def xform(self, inp):
    return inp
register(NullXform, 'null')

def read_file(filename):
  if filename == '-':
    return sys.stdin.read()
  else:
    with open(filename, "r", encoding='utf-8') as file:
      return file.read()

def write_file(filename, data):
  if filename == '-':
    sys.stdout.write(data)
  else:
    with open(filename, "w", encoding='utf-8') as file:
      file.write(data)

