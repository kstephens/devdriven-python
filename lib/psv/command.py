from typing import Any, Union, Type
import devdriven.cli.command as cmd
from devdriven.cli.types import Argv
from devdriven.cli.application import app

Input = Any

class Command(cmd.Command):
  def __call__(self, *args):
    return self.xform(*args)

  def xform(self, inp: Input, _env: dict) -> Any:
    return inp

  def make_xform(self, argv: Argv):  # -> Self:
    return main_make_xform(self.main, argv[0], argv[1:])

  def opt_name_key(self, name: str) -> str:
    return self.command_descriptor().options.opt_name_normalize(name) or name

def main_make_xform(main, klass_or_name: Union[str, Type], argv: Argv) -> Command:
  assert main
  if desc := app.descriptor(klass_or_name):
    xform = desc.klass()
    xform.set_main(main)
    xform.set_name(desc.name)
    xform.parse_argv(argv)
    return xform
  raise Exception(f'unknown command {klass_or_name!r}')

def section(name: str, order: int, *args):
  return app.begin_section(name, order, *args)

# Decorator
def command(klass):
  return app.command(klass)
