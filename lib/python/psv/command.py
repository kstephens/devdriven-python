from pathlib import Path
from dataclasses import dataclass, fields
import devdriven.cli
from devdriven.util import get_safe

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

# Decorator
def command(name, aliases, **kwargs):
  def wrapper(klass):
    assert issubclass(klass, Command)
    describe(klass, name, aliases, **kwargs)
    return klass
  return wrapper

DESCRIPTORS = []
DESCRIPTOR_BY_ANY = {}
DESCRIPTOR_BY_NAME = {}
DESCRIPTOR_BY_KLASS = {}

def descriptors():
  return DESCRIPTORS

def descriptor(name, default=None):
  return DESCRIPTOR_BY_NAME.get(name, default)

@dataclass
class Descriptor():
  name: str
  aliases: list
  synopsis: str
  description: str
  args: dict
  opts: dict
  content_type: str      # = None
  content_encoding: str  # = None
  preferred_suffix: str  # = None
  klass: object

def dataclass_from_dict(klass, opts):
    field_names = {f.name for f in fields(klass) if f.init}
    args = {k : v for k, v in opts.items() if k in field_names}
    return klass(**args)

def describe(klass, name, aliases, **kwargs):
  kwargs = {
    'synopsis': '',
    'description': '',
    'args': {},
    'opts': {},
    'content_type': None,
    'content_encoding': None,
    'preferred_suffix': '',
  } | kwargs | {
    "klass": klass,
    "name": name,
    "aliases": aliases,
  }
  desc = dataclass_from_dict(Descriptor, kwargs)
  for arg in [desc.name, *desc.aliases]:
    if assigned := descriptor(arg):
      raise Exception(f"describe: {arg!r} is already assigned to {assigned!r}")
    DESCRIPTOR_BY_NAME[arg] = DESCRIPTOR_BY_ANY[arg] = desc
  DESCRIPTOR_BY_KLASS[klass] = DESCRIPTOR_BY_ANY[klass] = desc
  DESCRIPTORS.append(desc)

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
