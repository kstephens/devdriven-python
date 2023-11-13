import re
from pathlib import Path
from dataclasses import dataclass
from typing import List
import devdriven.cli
from devdriven.util import get_safe, set_from_match, dataclass_from_dict, dataclass_from_dict, unpad_lines
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

  def to_dict(self):
    return [self.name, *self.argv]

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
    if args or kwargs:
      ic(klass)
      assert not args
      assert not kwargs
    describe(klass, args, kwargs)
    return klass
  return wrapper

@dataclass
class Descriptor():
  klass: object
  name: str
  aliases: list
  synopsis: str
  detail: list
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
    comments = []
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
      elif m := re.match(r'^[#] (.+)', line):
        comments.append(m[1])
      elif m := re.match(r'^\$ (.+)', line):
        self.examples.append(Example(command=m[1], comments=comments))
        comments = []
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
        self.detail.append(line)
      if debug:
        ic(m and m.groupdict())
    return self

@dataclass
class Example():
  command: str
  comments: List[str]

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
    'detail': [],
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

