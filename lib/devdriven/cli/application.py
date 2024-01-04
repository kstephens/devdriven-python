from itertools import chain
from devdriven.util import dataclass_from_dict
from devdriven.mime import short_and_long_suffix
from .options import Options
from .descriptor import Descriptor


# @dataclass
class Application:
  sections: list = []
  current_section: str = 'UNKNOWN'
  descriptors: list = []
  descriptor_by_any: dict = {}
  descriptor_by_name: dict = {}
  descriptor_by_klass: dict = {}

  def begin_section(self, name):
    assert name
    self.current_section = name
    if name not in self.sections:
      self.sections.append(name)

  def create_descriptor(self, klass):
    options = Options()
    kwargs = {
      'name': '',
      'brief': '',
      'synopsis': '',
      'aliases': [],
      'detail': [],
      'examples': [],
      'suffixes': '',
      'suffix_list': [],
    } | DEFAULTS | {
      'section': app.current_section,
      'klass': klass,
      'options': options,
    }
    return dataclass_from_dict(Descriptor, kwargs).parse_docstring(klass.__doc__)

  def descriptor(self, name_or_klass, default=None):
    return self.descriptor_by_any.get(name_or_klass, default)

  def descriptors_for_section(self, name):
    return [desc for desc in self.descriptors if desc.section == name]

  def descriptors_by_sections(self, secs=None):
    return list(chain.from_iterable([self.descriptors_for_section(sec) for sec in (secs or self.sections)]))

  def find_format(self, path, klass):
    short_suffix, long_suffix = short_and_long_suffix(path)
    valid_descs = [dsc for dsc in self.descriptors if issubclass(dsc.klass, klass)]
    for dsc in valid_descs:
      if long_suffix in dsc.suffix_list:
        return dsc.klass
    for dsc in valid_descs:
      if short_suffix in dsc.suffix_list:
        return dsc.klass
    return None

  def register(self, desc):
    for name in [desc.name, *desc.aliases]:
      if not name:
        raise Exception(f"Command: {desc.klass!r} : invalid name or alias")
      if assigned := self.descriptor(name):
        raise Exception(f"Command: {desc.klass!r} : {name!r} : is already assigned to {assigned!r}")
      self.descriptor_by_name[name] = self.descriptor_by_any[name] = desc
    self.descriptor_by_klass[desc.klass] = self.descriptor_by_any[desc.klass] = desc
    self.descriptors.append(desc)
    return desc

  # Decorator
  def command(self, klass):
    self.register(self.create_descriptor(klass))
    return klass


DEFAULTS = {
  'section': '',
  'content_type': None,
  'content_encoding': None,
  'suffixes': '',
}

app = Application()
