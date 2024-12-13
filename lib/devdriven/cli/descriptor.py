from typing import Any, Optional, Self, Type, List, Dict
import re
from dataclasses import dataclass, field
from .options import Options, make_options
from ..util import set_from_match, unpad_lines, trim_list


@dataclass
class Example:
    command: str
    comments: List[str]
    output: Optional[str] = field(default=None)


@dataclass
class Descriptor:
    klass: Type = field(default=object)
    name: str = field(default="")
    brief: str = field(default="")
    synopsis: str = field(default="")
    aliases: list = field(default_factory=list)
    detail: List[str] = field(default_factory=list)
    options: Options = field(default_factory=make_options)
    examples: List[Example] = field(default_factory=list)
    section: str = field(default="")
    metadata: Dict[str, Any] = field(default_factory=dict)
    synopsis_prefix: List[str] = field(default_factory=list)

    def parse_docstring(self, docstr: str) -> Self:
        found_aliases = False
        # debug = False
        lines = unpad_lines(re.sub(r"\\\n", "", docstr).splitlines())
        comments = []
        while lines:
            line = lines.pop(0)
            # if debug:
            #   ic(line)
            m = None
            if m := re.match(r"^:(?P<name>[a-z_]+)[:=] *(?P<value>.*)", line):
                self.metadata[m.group("name")] = m.group("value").strip()
            elif m := (
                re.match(r"^(?P<name>[-a-z]+) +- +(?P<brief>.+)", line)
                if not self.name
                else None
            ):
                set_from_match(self, m)
            elif m := (
                re.match(r"(?i)^Alias(?:es)?: +(.+)", line)
                if not found_aliases
                else None
            ):
                self.aliases.extend(re.split(r"\s*,\s*|\s+", m[1].strip()))
                found_aliases = True
            elif m := re.match(r"(?i)^(Arguments|Options|Examples):\s*$", line):
                # pylint: disable-next=pointless-statement
                None
            elif m := re.match(r"^[#] (.+)", line):
                comments.append(m[1])
            elif m := re.match(r"^\$ (.+)", line):
                self.examples.append(Example(command=m[1], comments=comments))
                comments = []
            elif self.options.parse_docstring(line):
                # if debug:
                #   ic((self.name, self.options))
                # pylint: disable-next=pointless-statement
                None
            else:
                self.detail.append(line)
            # if debug:
            #   ic(m and m.groupdict())
        self.build_synopsis()
        self.detail = trim_list(self.detail)
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
    example: Optional[Example]
    output: Optional[str] = field(default=None)
