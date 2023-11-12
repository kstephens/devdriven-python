import re
from pathlib import Path
from dataclasses import dataclass, fields
import devdriven.cli
from devdriven.util import get_safe
from icecream import ic

class Command(devdriven.cli.Command):
#  def parse_argv(self, argv):
#    super().parse_argv(argv)
#    return self

  def __call__(self, *args):
    return self.xform(*args)

  def xform(self, inp, _env):
    return inp

  def make_xform(self, argv):
    return main_make_xform(self.main, argv[0], argv[1:])

  def arg_or_opt(self, i, k, default):
    return get_safe(self.args, i, get_safe(self.opts, k, default))

  def command_descriptor(self):
    return DESCRIPTOR_BY_KLASS[self.__class__]

DESCRIPTORS = []
DESCRIPTOR_BY_ANY = {}
DESCRIPTOR_BY_NAME = {}
DESCRIPTOR_BY_KLASS = {}

def descriptors():
  return DESCRIPTORS

def descriptor(name, default=None):
  return DESCRIPTOR_BY_NAME.get(name, default)

def main_make_xform(main, klass_or_name, argv):
  assert main
  desc = DESCRIPTOR_BY_ANY.get(klass_or_name)
  if not desc:
    raise Exception(f'unknown command: {klass_or_name!r} : see help')
  xform = desc.klass()
  xform.set_main(main)
  xform.set_name(desc.name)
  xform.parse_argv(argv)
  return xform

def find_format(input_name, klass):
  for desc in descriptors():
    if issubclass(desc.klass, klass) and desc.preferred_suffix == Path(input_name).suffix:
      return desc.klass
  return None

# Decorator
def command(*args, **kwargs):
  def wrapper(klass):
    assert issubclass(klass, Command)
    describe(klass, args, kwargs)
    return klass
  return wrapper

@dataclass
class Descriptor():
  klass: object
  name: str
  aliases: list
  synopsis: str
  description: list
  args: dict
  opts: dict
  opt_aliases: dict
  examples: list
  section: str
  content_type: str      # = None
  content_encoding: str  # = None
  preferred_suffix: str  # = None
  data: object

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

  def parse_docstring(self, docstr):
    found_aliases = None
    debug = False
    lines = unpad_lines(docstr.splitlines())
    def eat_blanks():
      while lines and not lines[0]:
        lines.pop(0)
    while lines:
      line = lines.pop(0)
      if debug:
        ic(line)
      m = None
      if m := re.match(r'^:(?P<name>[a-z_]+)[:=] *(?P<value>.*)', line):
        setattr(self, m.group('name'), m.group('value').strip())
      elif m := not self.name and re.match(r'^(?P<name>[-a-z]+) +- +(?P<synopsis>.+)', line):
        set_from_match(self, m)
      elif m := not found_aliases and re.match(r'(?i)^Alias(?:es)?: +(.+)', line):
        self.aliases.extend(re.split(r'\s*,\s*|\s+', m[1].strip()))
        found_aliases = True
      elif m := re.match(r'(?i)^(Arguments|Options|Examples):\s*$', line):
        None
      elif m := re.match(r'(?i)^([#$] .*)', line):
        self.examples.append(m[1])
      elif m := re.match(r'^(--?[^:\|]+)[:\|] *(.*)', line):
        name, *opt_aliases = re.split(r', *', m[1].strip())
        if debug:
          ic((name, opt_aliases))
        self.opts[name] = m[2].strip()
        for opt_alias in opt_aliases:
          self.opt_aliases[opt_alias] = name
      elif m := re.match(r'^([^:\|]+)[:\|] *(.*)', line):
        self.args[m[1]] = m[2].strip()
      elif line:
        self.description.append(line)
      if debug:
        ic(m and m.groupdict())
      # ic(m and (m[0], m.groups()))
    return self

DEFAULTS = {
  'section': '',
  'content_type': None,
  'content_encoding': None,
  'preferred_suffix': '',
}

def describe(klass, args, kwargs):
  kwargs = {
    'name': '',
    'synopsis': '',
    'aliases': [],
    'description': [],
    'args': {},
    'opts': {},
    'opt_aliases': {},
    'examples': [],
  } | DEFAULTS | kwargs | {
    "klass": klass,
  }
  if klass.__doc__:
    dataclass_from_dict(Descriptor, kwargs).parse_docstring(klass.__doc__).register()
  else:
    raise Exception(f'Missing __doc__ string : {klass!r}')
    kwargs = kwargs | {
      "name": args[0],
      "aliases": args[1],
    }
    dataclass_from_dict(Descriptor, kwargs).register()

def set_from_match(object, match : re.Match):
  setattr_from_dict(object, match.groupdict())

def setattr_from_dict(object, attrs):
  for name, val in attrs.items():
    setattr(object, name, val)
def dataclass_from_dict(klass, opts, defaults=None):
  defaults = defaults or {}
  args = {f.name: opts.get(f.name, defaults.get(f.name, None))
          for f in fields(klass) if f.init}
  return klass(**args)

def unpad_lines(lines):
  lines = lines.copy()
  while lines and not lines[0]:
    lines.pop(0)
  for line in lines:
    if m := re.match(r'^( +)', line):
      pad = re.compile(f'^{m[1]}')
      break
  return [re.sub(pad, '', line) for line in lines]

def fullname(o):
  klass = o.__class__
  module = klass.__module__
  if module == 'builtins':
      return klass.__qualname__ # avoid outputs like 'builtins.str'
  return module + '.' + klass.__qualname__
