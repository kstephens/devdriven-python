print(__file__); print(__name__)

import sys
import devdriven.cli

class Base(devdriven.cli.Command):
  def parse_argv(self, argv):
    ic(argv)
    super().parse_argv(argv)
    return self

  def __call__(*args):
    return self.xform(*args)

  def xform(self, inp):
    return inp

  def read_file(self, filename):
    if filename == '-':
      return sys.stdin.read()
    else:
      with open(filename, "r", encoding='utf-8') as file:
        return file.read()

  def write_file(self, filename, data):
    if filename == '-':
      sys.stdout.write(data)
    else:
      with open(filename, "w", encoding='utf-8') as file:
        file.write(data)

  def make_xform(self, argv):
    name = argv[0]
    argv = argv[1:]
    return main_make_xform(self.main, name, argv)

CONSTRUCTOR_FOR_NAME = {}
def register(constructor, *names):
  print(f'register({constructor!r}, {names!r}')
  for name in names:
    if name in CONSTRUCTOR_FOR_NAME:
      raise Exception(f"register: {name!r} is already assigned to {CONSTRUCTOR_FOR_NAME[name]!r}")
    CONSTRUCTOR_FOR_NAME[name] = constructor
  ic(CONSTRUCTOR_FOR_NAME)

def main_make_xform(main, name, argv):
  xform = CONSTRUCTOR_FOR_NAME[name]()
  xform.set_main(main)
  xform.set_name(name)
  ic(xform)
  return xform.parse_argv(argv)
