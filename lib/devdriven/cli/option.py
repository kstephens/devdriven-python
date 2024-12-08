from typing import Any, Self, Optional, List
import re
from dataclasses import dataclass, field


@dataclass
class Argument:
    style: str = field(default="")
    kind: str = field(default="")
    name: str = field(default="")
    description: str = field(default="")
    # optional: bool = field(default=False)
    default: Optional[str] = field(default=None)
    value: Optional[Any] = field(default=None)


@dataclass
class Option(Argument):
    arg: str = field(default="")
    full: str = field(default="")
    aliases: List[Any] = field(default_factory=list)
    alias_of: Optional[str] = field(default=None)

    def parse_arg(self, arg: str) -> Optional[Self]:
        self.style = "arg"
        self.aliases = []
        return self.parse_simple(arg)

    def parse_doc(self, arg: str) -> Optional[Self]:
        self.style = "doc"
        self.aliases = []
        if m := re.match(r"^(?:.+  |)Default: +(.+?)\.$", arg):
            self.default = m[1].strip()
        if m := re.match(r"^([^\|]+?)  \|  (.*)", arg):
            opts = re.split(r", ", m[1].strip())
            arg, self.description = opts.pop(0), m[2].strip()
            for opt in opts:
                self.aliases.append(self.parse_alias(opt, self))
        if result := self.parse_simple(arg):
            for alias in self.aliases:
                alias.kind = self.kind
                alias.alias_of = self.name
        return result

    def parse_alias(self, opt: str, target: Self):
        alias = Option().parse_simple(opt)
        assert alias is not None, "parse_alias: expected simple option"
        alias.style = target.style
        alias.kind = target.kind
        alias.aliases = []
        alias.description = target.description
        alias.default = target.default
        return alias

    def parse_simple(self, arg: str) -> Optional[Self]:
        def matched_long(kind, name, val):
            self.arg = arg
            self.kind, self.full, self.name, self.value = kind, f"--{name}", name, val
            return self

        def matched_flag(opt, kind, name, val):
            self.arg = arg
            opt.kind, opt.full, opt.name, opt.value = kind, f"-{name}", name, val
            return opt

        def matched_flags(kind, flags, val):
            flags = [*flags]
            matched_flag(self, kind, flags.pop(0), val)
            for flag in flags:
                self.aliases.append(matched_flag(Option(), kind, flag, val))
            return self

        if m := re.match(r"^--([a-zA-Z][-_a-zA-Z0-9]*)=(.*)$", arg):
            return matched_long("option", m[1], m[2])
        if m := re.match(r"^--no-([a-zA-Z][-_a-zA-Z0-9]+)$", arg):
            return matched_long("flag", m[1], False)
        if m := re.match(r"^--([a-zA-Z][-_a-zA-Z0-9]+)$", arg):
            return matched_long("flag", m[1], True)
        if m := re.match(r"^\+\+([a-zA-Z][-_a-zA-Z0-9]+)$", arg):
            return matched_long("flag", m[1], False)
        if m := re.match(r"^-([a-zA-Z][-_a-zA-Z0-9]*)$", arg):
            return matched_flags("flag", m[1], True)
        if m := re.match(r"^\+([a-zA-Z][-_a-zA-Z0-9]*)$", arg):
            return matched_flags("flag", m[1], False)
        return None

    def synopsis(self) -> str:
        assert self.aliases is not None
        return ", ".join([self.arg] + [opt.full for opt in self.aliases])


def make_option(**kwargs) -> Option:
    return Option(**kwargs)
