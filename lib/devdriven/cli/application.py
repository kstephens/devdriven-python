from typing import Type, List, Dict
import logging
from .descriptor import Descriptor, Section, SectionDescriptorExample


class Application:
    sections: List[Section] = []
    section_by_name: Dict[str, Section] = {}
    current_section: Section
    descriptors: list = []
    descriptor_by_any: dict = {}
    descriptor_by_name: dict = {}
    descriptor_by_klass: dict = {}
    synopsis_prefix: list = []

    def begin_section(self, name: str, order: int) -> None:
        if section := self.section_by_name.get(name):
            assert (name, order) == (section.name, section.order)
        else:
            section = Section(name, order)
            if conflicts := [
                (sec.name, sec.order) for sec in self.sections if sec.order == order
            ]:
                raise AttributeError(f"order conflict : {section!r} with {conflicts!r}")
            self.sections.append(section)
            self.section_by_name[name] = section
        self.sections.sort(key=lambda s: s.order)
        self.current_section = section

    def create_descriptor(self, klass: Type) -> Descriptor:
        kwargs = {
            "name": "",
            "section": app.current_section.name,
            "klass": klass,
            "synopsis_prefix": self.synopsis_prefix,
        }
        docstr = klass.__doc__
        assert docstr is not None
        try:
            return Descriptor(**kwargs).parse_docstring(docstr)
        except Exception as exc:
            logging.fatal(
                "Could not parse %s docstring : %s : \n%s",
                repr(klass),
                repr(exc),
                docstr,
            )
            raise exc

    def descriptor(self, name_or_klass: str | Type, default=None) -> Descriptor:
        return self.descriptor_by_any.get(name_or_klass, default)

    def descriptors_for_section(self, name: str) -> List[Descriptor]:
        return self.section_by_name[name].descriptors

    def descriptors_by_sections(self, secs=None) -> List[Descriptor]:
        return sum([sec.descriptors for sec in (secs or self.sections)], [])

    def register(self, desc: Descriptor) -> Descriptor:
        for name in [desc.name, *desc.aliases]:
            if not name:
                raise Exception(f"Command: {desc.klass!r} : invalid name or alias")
            if assigned := self.descriptor(name):
                raise Exception(
                    f"Command: {desc.klass!r} : {name!r} : is already assigned to {assigned!r}"
                )
            self.descriptor_by_name[name] = self.descriptor_by_any[name] = desc
        self.descriptor_by_klass[desc.klass] = self.descriptor_by_any[desc.klass] = desc
        self.descriptors.append(desc)
        self.current_section.descriptors.append(desc)
        return desc

    def enumerate_descriptors(self) -> List[SectionDescriptorExample]:
        return [
            SectionDescriptorExample(sec, dsc, None)
            for sec in self.sections
            for dsc in sec.descriptors
        ]

    def enumerate_examples(self) -> List[SectionDescriptorExample]:
        return [
            SectionDescriptorExample(sec, dsc, exa)
            for sec in self.sections
            for dsc in sec.descriptors
            for exa in dsc.examples
        ]

    # Decorator
    def command(self, klass: Type):
        self.register(self.create_descriptor(klass))
        return klass


DEFAULTS = {
    "section": "",
}

app = Application()
