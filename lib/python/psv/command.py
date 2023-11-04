import devdriven.cli
from devdriven.util import get_safe

class Command(devdriven.cli.Command):
#  def parse_argv(self, argv):
#    super().parse_argv(argv)
#    return self

  def __call__(self, *args):
    return self.xform(*args)

  def xform(self, inp, _env):
    return inp

  def make_xform(self, argv):
    name = argv[0]
    argv = argv[1:]
    return main_make_xform(self.main, name, argv)

  def arg_or_opt(self, i, k, default):
    return get_safe(self.args, i, get_safe(self.opts, k, default))

  def command_descriptor(self):
    return DESCRIPTOR_BY_CONSTRUCTOR[self.__class__]

DESCRIPTORS = []
def descriptors():
  return DESCRIPTORS

DESCRIPTOR_BY_NAME = {}
DESCRIPTOR_BY_CONSTRUCTOR = {}
def descriptor(name, default=None):
  return DESCRIPTOR_BY_NAME.get(name, default)

def register(constructor, name, aliases, **kwargs):
  desc = {
    'synopsis': '',
    'args': {},
    'opts': {},
    } | kwargs | {
      "constructor": constructor,
      "name": name,
      "aliases": aliases,
    }
  for arg in [name, *aliases]:
    if assigned := descriptor(arg):
      raise Exception(f"register: {arg!r} is already assigned to {assigned!r}")
    DESCRIPTOR_BY_NAME[arg] = desc
  DESCRIPTOR_BY_CONSTRUCTOR[constructor] = desc
  DESCRIPTORS.append(desc)

def main_make_xform(main, name, argv):
  assert main
  if name not in DESCRIPTOR_BY_NAME:
    raise Exception(f'unknown command: {name!r} : see help')
  xform = DESCRIPTOR_BY_NAME[name]['constructor']()
  xform.set_main(main)
  xform.set_name(name)
  xform.parse_argv(argv)
  return xform
