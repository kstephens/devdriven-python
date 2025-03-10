from typing import Any, Self, List, Dict
import re
import inspect
from dataclasses import dataclass, field
from ..util import get_safe
from .option import Option, make_option
from .types import Argv


@dataclass
class Options:
    argv: Argv = field(default_factory=list)
    args: Argv = field(default_factory=list)
    args_synopsis: str = field(default="")
    arg_by_name: Dict[str, str] = field(default_factory=dict)
    opts: List[Option] = field(default_factory=list)
    opt_by_name: Dict[str, Option] = field(default_factory=dict)
    opts_defaults: Dict[str, Any] = field(default_factory=dict)
    opt_char_map: Dict[str, str] = field(default_factory=dict)
    opt_aliases: Dict[str, Option] = field(default_factory=dict)
    delegate: Any = None

    def parse_argv(self, argv: Argv) -> Self:
        self.argv = argv.copy()
        while argv:
            arg = argv.pop(0)
            if arg == "--":
                self.args.extend(argv)
                break

            if self.args:
                self.args.append(arg)
            elif opt := make_option().parse_arg(arg):
                self.opts.append(opt)
                self.opt_by_name[opt.name] = opt
                self.set_opt(opt.name, opt.value)
                for alias in opt.aliases:
                    self.opts.append(alias)
                    self.opt_by_name[alias.name] = alias
                    self.set_opt(alias.name, opt.value)
                opt.aliases = []
            else:
                self.args.append(arg)
        return self

    def set_opt(self, name: str, val: Any) -> None:
        key = self.opt_name_key(name)
        if key and self.opt_valid(key, val):
            self.opt_by_name[key].value = val
        else:
            raise Exception(f"Invalid option : {name!r}")

    def opt(self, key, *default) -> Any:
        if isinstance(key, tuple) and key:
            return self.opt(key[0], self.opt(key[1:], *default))
        assert isinstance(key, str)
        if opt := self.opt_by_name.get(key):
            return opt.value
        if default:
            return default[0]
        return self.opt_default(key)

    def arg_or_opt(self, i: int, k: str, default: Any) -> Any:
        return get_safe(self.args, i, get_safe(self.opt_by_name, k, default))

    def opt_valid(self, name: str, val: Any) -> Any:
        return self.maybe_delegate("opt_valid", True, name, val)

    def opt_default(self, name: str) -> Any:
        return self.maybe_delegate("opt_default", self.opts_defaults.get(name), name)

    def opt_name_key(self, name: str) -> str | None:
        return self.maybe_delegate(
            "opt_name_key", self.opt_char_map.get(name, name), name
        )

    def opt_name_normalize(self, name: str) -> str | None:
        if opt := self.opt_by_name.get(name):
            return opt.name
        if alias := self.opt_aliases.get(name):
            return alias.alias_of
        return None

    # See: Descriptor
    def parse_docstring(self, line: str) -> Self | None:
        m = None

        def add_arg(m):
            name = m[1].strip()
            self.arg_by_name[name] = m[2].strip()
            self.args.append(name)

        try:
            if m := re.match(r"^(-) +[\|] *(.*)", line):
                add_arg(m)
                return self
            if option := make_option().parse_doc(line):
                self.opt_by_name[option.name] = option
                self.opts.append(option)
                for alias in option.aliases:
                    self.opt_aliases[alias.name] = alias
                return self
            if m := re.match(r"^([^\|]+)[\|] *(.*)", line):
                add_arg(m)
                return self
            return None
        # finally:
        #  pass
        except Exception as e:
            raise Exception(
                f"parse_docstring: could not parse : {line!r} : {e!r}"
            ) from e

    def command_synopsis(self) -> Argv:
        cmd = []
        for opt in self.opts:
            opts = [opt.arg]  # + [alias.full for alias in opt.aliases]
            cmd.append(f'[{", ".join(opts)}]')
        for arg in self.args:
            if arg.endswith(" ...") or len(self.args) > 1:
                arg = f"[{arg}]"
            cmd.append(arg)
        return cmd

    def get_opt(self, name: str, aliases=False) -> Option | None:
        for opt in self.opts:
            if opt.name == name:
                return opt
            if aliases and name in opt.aliases:
                return opt
        return None

    def get_opt_aliases(self, opt) -> List[Any]:
        return [k for k, v in self.opt_aliases.items() if v == opt]

    def maybe_delegate(self, name: str, default: Any, *args) -> Any:
        if self.delegate and hasattr(self.delegate, name):
            attr = getattr(self, name)
            if inspect.ismethod(attr):
                return attr(*args)
        return default


def make_options(**kwargs) -> Options:
    return Options(**kwargs)
