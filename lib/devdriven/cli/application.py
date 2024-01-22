from typing import Union, Optional, Type, List, Dict
from devdriven.util import dataclass_from_dict
from devdriven.mime import short_and_long_suffix
from .options import Options
from .descriptor import Descriptor, Section

class Application:
  sections: List[Section] = []
  section_by_name: Dict[str, Section] = {}
  current_section: Section
  descriptors: list = []
  descriptor_by_any: dict = {}
  descriptor_by_name: dict = {}
  descriptor_by_klass: dict = {}

  def begin_section(self, name: str, order: int) -> None:
    assert name
    if section := self.section_by_name.get(name):
      assert (name, order) == (section.name, section.order)
    else:
      section = Section(name, order)
      self.sections.append(section)
      self.section_by_name[name] = section
    self.sections.sort(key=lambda s: s.order)
    self.current_section = section

  def create_descriptor(self, klass: Type) -> Descriptor:
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
      'section': app.current_section.name,
      'klass': klass,
      'options': options,
    }
    return dataclass_from_dict(Descriptor, kwargs).parse_docstring(klass.__doc__)

  def descriptor(self, name_or_klass: Union[str, Type], default=None) -> Descriptor:
    return self.descriptor_by_any.get(name_or_klass, default)

  def descriptors_for_section(self, name: str) -> List[Descriptor]:
    return self.sections[name].descriptors

  def descriptors_by_sections(self, secs=None) -> List[Descriptor]:
    return sum([sec.descriptors for sec in (secs or self.sections)], [])

  def find_format(self, path: str, klass: Type) -> Optional[Type]:
    short_suffix, long_suffix = short_and_long_suffix(path)
    valid_descs = [dsc for dsc in self.descriptors if issubclass(dsc.klass, klass)]
    for dsc in valid_descs:
      if long_suffix in dsc.suffix_list:
        return dsc.klass
    for dsc in valid_descs:
      if short_suffix in dsc.suffix_list:
        return dsc.klass
    return None

  def register(self, desc: Descriptor) -> Descriptor:
    for name in [desc.name, *desc.aliases]:
      if not name:
        raise Exception(f"Command: {desc.klass!r} : invalid name or alias")
      if assigned := self.descriptor(name):
        raise Exception(f"Command: {desc.klass!r} : {name!r} : is already assigned to {assigned!r}")
      self.descriptor_by_name[name] = self.descriptor_by_any[name] = desc
    self.descriptor_by_klass[desc.klass] = self.descriptor_by_any[desc.klass] = desc
    self.descriptors.append(desc)
    self.current_section.descriptors.append(desc)
    return desc

  # Decorator
  def command(self, klass: Type):
    self.register(self.create_descriptor(klass))
    return klass


DEFAULTS = {
  'section': '',
  'content_type': None,
  'content_encoding': None,
  'suffixes': '',
}

app = Application()
