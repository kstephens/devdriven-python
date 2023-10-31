import devdriven.cli

class Base(devdriven.cli.Command):
#  def parse_argv(self, argv):
#    super().parse_argv(argv)
#    return self

  def __call__(self, *args):
    return self.xform(*args)

  def xform(self, inp):
    return inp

  def make_xform(self, argv):
    name = argv[0]
    argv = argv[1:]
    return main_make_xform(self.main, name, argv)

DESCRIPTORS = []
def descriptors():
  return DESCRIPTORS
DESCRIPTOR_BY_NAME = {}
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
  DESCRIPTORS.append(desc)
  for name in [name, *aliases]:
    if name in DESCRIPTOR_BY_NAME:
      raise Exception(f"register: {name!r} is already assigned to {DESCRIPTOR_BY_NAME[name]!r}")
    DESCRIPTOR_BY_NAME[name] = desc

def main_make_xform(main, name, argv):
  xform = DESCRIPTOR_BY_NAME[name]['constructor']()
  xform.set_main(main)
  xform.set_name(name)
  xform.parse_argv(argv)
  return xform
