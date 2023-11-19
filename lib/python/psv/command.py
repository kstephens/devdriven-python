import devdriven.cli.command as cmd
import devdriven.cli.descriptor as desc
from itertools import chain

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

def begin_section(name):
  return desc.begin_section(name)

def sections():
  return desc.sections()

def descriptors_for_section(name):
  return cmd.descriptors_for_section(name)

def descriptors_by_sections(secs=None):
  return list(chain.from_iterable([descriptors_for_section(sec) for sec in sections()]))

# Decorator
def command(klass):
  return cmd.command(klass)

