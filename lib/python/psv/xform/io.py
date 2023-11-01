from .base import Base, register
from pathlib import Path
import sys

class Paths():
  def __init__(self, paths):
    self.paths = list(map(Path, paths))
    self.str = None
  def __repr__(self):
    return f'Paths({self.paths!r})'
  def to_dict(self):
    return ['Paths:', list(map(str, self.paths))]
  def __str__(self):
    if not self.str:
      self.str = ''.join(map(read_file, self.paths))
    return self.str

class IoIn(Base):
  def xform(self, _inp, env):
    if not self.args:
      self.args.append('-')
    path = Path(self.args[0])
    env['input.paths'] = [ str(path) ]
    return path
register(IoIn, 'in', ['i'],
         synopsis="Read input.",
         args={"FILE ...": "input files.",
               "-": "denotes stdin"})

class IoOut(Base):
  def xform(self, inp, env):
    if inp is None:
      return None
    inp = str(inp)
    if not self.args:
      self.args.append('-')
    env['output.paths'] = list(map(str, self.args))
    for arg in self.args:
      write_file(arg, inp)
    return None
register(IoOut, 'out', ['o'],
         synopsis="Write output.",
         args={"FILE ...": "output files.",
               "-": "denotes stdout"})

def read_file(filename, encoding='utf-8'):
  if isinstance(filename, Path):
    filename = str(filename)
  if filename == '-':
    return sys.stdin.read().decode(encoding)
  with open(filename, "r", encoding=encoding) as file:
    return file.read()

def write_file(filename, data):
  if isinstance(filename, Path):
    filename = str(filename)
  if filename == '-':
    sys.stdout.write(data)
  else:
    with open(filename, "w", encoding='utf-8') as file:
      file.write(data)

