from typing import Any, Self, Type
import logging
from devdriven.util import get_safe
from devdriven.cli.types import Argv
from .descriptor import Descriptor
from .option import Option
# import devdriven.cli.descriptor as desc
from .application import app

class Command:
  def __init__(self):
    self.main = None
    self.argv = []
    self.name = None
    self.args = []
    self.opts = {}
    self.opts_defaults = {}
    self.opt_char_map = {}
    self.rtn = None

  def log(self, level, fmt, *args):
    getattr(logging, level)('%s : ' + fmt, self.name, *args)

  def run(self, argv):
    self.parse_argv(argv)
    self.exec()

  def parse_argv(self, argv):
    self.argv = argv.copy()
    while argv:
      arg = argv.pop(0)
      if arg == '--':
        self.args.extend(argv)
        break
      if self.args:
        self.args.append(arg)
      elif opt := Option().parse_arg(arg):
        self.set_opt(opt.name, opt.value)
        for alias in opt.aliases:
          self.set_opt(alias.name, opt.value)
      else:
        self.args.append(arg)
    return self

  def set_name(self, name):
    self.name = name
    return self

  def set_main(self, main):
    self.main = main
    return self

  def set_opt(self, name, val):
    key = self.opt_name_key(name)
    if self.opt_valid(key, val):
      self.opts[key] = val
    else:
      raise Exception(f'Invalid option : {name!r}')

  def opt(self, name: str, *default) -> Any:
    if not isinstance(name, str):
      raise TypeError(f'Invalid option : {name!r}')
    if name in self.opts:
      return self.opts[name]
    if default:
      return default[0]
    return self.opt_default(name)

  def arg_or_opt(self, i, k, default):
    return get_safe(self.args, i, get_safe(self.opts, k, default))

  def command_descriptor(self):
    return app.descriptor(self.__class__)

  def to_dict(self):
    return [self.name, *self.argv]

  # OVERRIDE:
  def opt_valid(self, _key, _val):
    return True

  def opt_default(self, key):
    return self.opts_defaults.get(key, None)

  def opt_name_key(self, name):
    return self.opt_char_map.get(name, name)

  # OVERRIDE:
  def exec(self):
    return self.rtn

# Decorator
def command(klass):
  assert issubclass(klass, Command)
  app.command(klass)
  return klass
