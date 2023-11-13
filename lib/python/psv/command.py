import devdriven.cli.command as cmd

class Command(cmd.Command):
#  def parse_argv(self, argv):
#    super().parse_argv(argv)
#    return self

  def __call__(self, *args):
    return self.xform(*args)

  def xform(self, inp, _env):
    return inp

  def make_xform(self, argv):
    return main_make_xform(self.main, argv[0], argv[1:])

def main_make_xform(main, klass_or_name, argv):
  assert main
  d = cmd.descriptor(klass_or_name)
  xform = d.klass()
  xform.set_main(main)
  xform.set_name(d.name)
  xform.parse_argv(argv)
  return xform

def find_format(*args):
  return cmd.find_format(*args)

# Decorator
def command():
  return cmd.command()
