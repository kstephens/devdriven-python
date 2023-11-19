import re
import logging
from pathlib import Path
from devdriven.util import get_safe
import devdriven.cli.descriptor as desc
from devdriven.cli.option import Option

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
    getattr(logging, level)(f'%s : ' + fmt, self.name, *args)

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

  def opt(self, key, *default):
    if isinstance(key, tuple) and key:
      return self.opt(key[0], self.opt(key[1:], *default))
    if key in self.opts:
      return self.opts[key]
    if default:
      return default[0]
    return self.opt_default(key)

  def arg_or_opt(self, i, k, default):
    return get_safe(self.args, i, get_safe(self.opts, k, default))

  def command_descriptor(self):
    return descriptor(self.__class__)

  def to_dict(self):
    return [self.name, *self.argv]

  # OVERRIDE:
  def opt_valid(self, _key, _val):
    return True

  def opt_default(self, key):
    return self.opts_defaults.get(key, None)

  def opt_name_key(self, flag):
    return self.opt_char_map.get(flag, flag)

  # OVERRIDE:
  def exec(self):
    return self.rtn

DESCRIPTORS = []
DESCRIPTOR_BY_ANY = {}
DESCRIPTOR_BY_NAME = {}
DESCRIPTOR_BY_KLASS = {}

def descriptors():
  return DESCRIPTORS

def descriptor(name_or_klass, default=None):
  return DESCRIPTOR_BY_ANY.get(name_or_klass, default)

def descriptors_for_section(name):
  return [desc for desc in descriptors() if desc.section == name]

def find_format(path, klass):
  short_suffix = long_suffix = Path(path).suffix
  if m := re.match(r'(?:^|/)[^.]+(\.[^/]+)$', str(path)):
    long_suffix = m[1]
  for dsc in descriptors():
    if issubclass(dsc.klass, klass) and dsc.preferred_suffix == long_suffix:
      return dsc.klass
  for dsc in descriptors():
    if issubclass(dsc.klass, klass) and dsc.preferred_suffix == short_suffix:
      return dsc.klass
  return None

def register(self):
  for name in [self.name, *self.aliases]:
    if not name:
      raise Exception(f"Command: {self.klass!r} : invalid name or alias")
    if assigned := descriptor(name):
      raise Exception(f"Command: {self.klass!r} : {name!r} : is already assigned to {assigned!r}")
    DESCRIPTOR_BY_NAME[name] = DESCRIPTOR_BY_ANY[name] = self
  DESCRIPTOR_BY_KLASS[self.klass] = DESCRIPTOR_BY_ANY[self.klass] = self
  DESCRIPTORS.append(self)
  return self

# Decorator
def command():
  def wrapper(klass):
    assert issubclass(klass, Command)
    register(desc.create_descriptor(klass))
    return klass
  return wrapper
