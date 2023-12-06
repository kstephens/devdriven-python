import devdriven.cli.command as cmd
from devdriven.cli.application import app

class Command(cmd.Command):
  def __call__(self, *args):
    return self.xform(*args)

  def xform(self, inp, _env):
    return inp

  def make_xform(self, argv):
    return main_make_xform(self.main, argv[0], argv[1:])

def main_make_xform(main, klass_or_name, argv):
  assert main
  if d := app.descriptor(klass_or_name):
    xform = d.klass()
    xform.set_main(main)
    xform.set_name(d.name)
    xform.parse_argv(argv)
    return xform
  raise Exception(f'unknown command {klass_or_name!r}')

def section(name):
  return app.begin_section(name)

# Decorator
def command(klass):
  return app.command(klass)
