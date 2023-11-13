import re
from pathlib import Path
from devdriven.util import get_safe
import devdriven.cli.descriptor as desc

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
      elif mtch := re.match(r'^--([a-zA-Z][-_a-zA-Z0-9]*)=(.*)$', arg):
        self.set_opt(mtch.group(1), mtch.group(2))
      elif mtch := re.match(r'^--([a-zA-Z][-_a-zA-Z0-9]*)$', arg):
        self.set_opt(mtch.group(1), True)
      elif mtch := re.match(r'^\+\+([a-zA-Z][-_a-zA-Z0-9]*)$', arg):
        self.set_opt(mtch.group(1), False)
      elif mtch := re.match(r'^-([a-zA-Z][-_a-zA-Z0-9]*)$', arg):
        for flag in [*mtch.group(1)]:
          self.set_opt(flag, True)
      elif mtch := re.match(r'^\+([a-zA-Z][-_a-zA-Z0-9]*)$', arg):
        for flag in [*mtch.group(1)]:
          self.set_opt(flag, False)
      else:
        self.args.append(arg)
    return self

  def set_name(self, name):
    self.name = name
    return self

  def set_main(self, main):
    self.main = main
    return self

  def set_opt(self, name, val, arg=None):
    key = self.opt_name_key(name)
    if self.opt_valid(key, val):
      self.opts[key] = val
    else:
      raise Exception(f'Invalid option : {name!r}')

  def opt(self, key, *default):
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

def find_format(path, klass):
  for dsc in descriptors():
    if issubclass(dsc.klass, klass) and dsc.preferred_suffix == Path(path).suffix:
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
