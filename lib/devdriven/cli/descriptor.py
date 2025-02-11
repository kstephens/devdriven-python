from typing import Any, Self, Type, List, Dict
import re
from dataclasses import dataclass, field
from .options import Options, make_options
from ..util import set_from_match, unpad_lines, trim_list


@dataclass
class Example:
    command: str
    comments: List[str]
    output: str | None = field(default=None)


class Descriptor:
    klass: Type
    name: str
    brief: str
    synopsis: str
    aliases: list
    detail: List[str]
    options: Options
    examples: List[Example]
    section: str
    metadata: Dict[str, Any]
    synopsis_prefix: List[str]

    def __init__(self, **kwargs):
        self.klass = None
        self.name = ""
        self.brief = ""
        self.synposis = ""
        self.detail = []
        self.aliases = []
        self.options = make_options()
        self.examples = []
        self.section = ""
        self.metadata = {}
        self.synopsis_prefix = []
        for k, v in kwargs.items():
            setattr(self, k, v)

    def parse_docstring(self, docstr: str) -> Self:
        found_aliases = False
        # debug = False
        lines = unpad_lines(re.sub(r"\\\n", "", docstr).splitlines())
        lines = [re.sub(r"\s+$", "", line) for line in lines]
        # ic(lines)
        comments = []
        while lines:
            line = lines.pop(0)
            # ic(line)
            m = None
            if m := re.search(r"^\s*:(?P<name>[a-z_]+)[:=] *(?P<value>.*)", line):
                self.metadata[m["name"]] = m["value"].strip()
            elif m := (
                re.search(r"^\s*(?P<name>[-a-z]+) +- +(?P<brief>.+)", line)
                if not self.name
                else None
            ):
                set_from_match(self, m)
            elif m := (
                re.match(r"(?i)^\s*Alias(?:es)?: +(.+)", line)
                if not found_aliases
                else None
            ):
                self.aliases.extend(re.split(r"\s*,\s*|\s+", m[1].strip()))
                found_aliases = True
            elif m := re.search(r"(?i)^\s*(Arguments|Options|Examples):\s*$", line):
                pass
            elif m := re.search(r"^\s*[#] (.+)", line):
                comments.append(m[1])
            elif m := re.search(r"^\s*\$ (.+)", line):
                self.examples.append(Example(command=m[1], comments=comments))
                comments = []
            elif self.options.parse_docstring(line):
                pass
            #            elif not re.search(r"^\s*$", line):
            else:
                self.detail.append(line)
        self.build_synopsis()
        self.detail = trim_list(self.detail)
        # ic(self.detail)
        # ic(self.examples)
        # ic(self.synopsis)
        return self

    def get_opt_aliases(self, opt):
        return self.options.get_opt_aliases(opt)

    def build_synopsis(self) -> None:
        assert isinstance(self.options, Options)
        cmd = self.command_path() + self.options.command_synopsis()
        self.synopsis = " ".join([x.strip() for x in cmd]).strip()

    def command_path(self) -> List[str]:
        return self.synopsis_prefix + [self.name]


def make_descriptor(**kwargs) -> Descriptor:
    return Descriptor(**kwargs)


@dataclass
class Section:
    name: str = "UNKNOWN"
    order: int = -1
    descriptors: List[Descriptor] = field(default_factory=list)


@dataclass
class SectionDescriptorExample:
    section: Section
    descriptor: Descriptor
    example: Example | None
    output: str | None = field(default=None)
