from pathlib import Path
import sys
from .content import Content
from .command import Command, register

class IoIn(Command):
  def xform(self, _inp, env):
    if not self.args:
      self.args.append('-')
    content = Content(self.args[0])
    env['input.paths'] = [self.args[0]]
    return content
register(IoIn, 'in', ['i', '-i'],
         synopsis="Read input.",
         args={"FILE ...": "input files.",
               "-": "denotes stdin"})

class IoOut(Command):
  def xform(self, inp, env):
    if inp is None:
      return None
    inp = str(inp)
    if not self.args:
      self.args.append('-')
    env['output.paths'] = list(map(str, self.args))
    for arg in self.args:
      write_data(arg, inp)
    return None
register(IoOut, 'out', ['o', 'o-'],
         synopsis="Write output.",
         args={"FILE ...": "output files.",
               "-": "denotes stdout"})

def read_data(content, encoding='utf-8'):
  if isinstance(filename, Path):
    filename = str(filename)
  if filename == '-':
    return sys.stdin.read().decode(encoding)
  with open(filename, "r", encoding=encoding) as file:
    return file.read()

def write_data(filename, data):
  if isinstance(filename, Path):
    filename = str(filename)
  if filename == '-':
    sys.stdout.write(data)
  else:
    with open(filename, "w", encoding='utf-8') as file:
      file.write(data)
