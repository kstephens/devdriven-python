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

CONSTRUCTOR_FOR_NAME = {}
def register(constructor, *names):
  for name in names:
    if name in CONSTRUCTOR_FOR_NAME:
      raise Exception(f"register: {name!r} is already assigned to {CONSTRUCTOR_FOR_NAME[name]!r}")
    CONSTRUCTOR_FOR_NAME[name] = constructor

def main_make_xform(main, name, argv):
  xform = CONSTRUCTOR_FOR_NAME[name]()
  xform.set_main(main)
  xform.set_name(name)
  xform.parse_argv(argv)
  return xform
