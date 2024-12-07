from typing import Any, Self, Optional, List, Dict
from optparse import OptionParser
import re
from dataclasses import dataclass, field
from devdriven.util import get_safe
from devdriven.cli.command import Command
from devdriven.cli.option import Option
from devdriven.cli.options import Options
from devdriven.cli.types import Argv


class Parser:

    def __init__(self):
        self.option_parser = OptionParser()

    # From Command.parse_argv():
    # This is almost exactly parse_options_argv()
    def parse_command_argv(self, command: Command, argv: Argv):
        command.argv = argv.copy()
        while argv:
            arg = argv.pop(0)
            if arg == "--":
                command.args.extend(argv)
                break
            if command.args:
                command.args.append(arg)
            elif option := self.parse_option_arg(Option(**{}), arg):
                command.set_opt(option.name, option.value)
                for alias in option.aliases:
                    command.set_opt(alias.name, option.value)
            else:
                command.args.append(arg)
        return command

    # From Options.parse_argv():
    def parse_options_argv(self, options: Options, argv: Argv) -> Options:
        options.argv = argv.copy()
        # options.args = []
        while argv:
            arg = argv.pop(0)
            # Consume all args after "--":
            if arg == "--":
                options.args.extend(argv)
                break
            # Stop parsing options after first arg:
            if options.args:
                options.args.append(arg)
            # Attempt to parse option:
            elif option := self.parse_option_arg(Option(**{}), arg):
                options.opts.append(option)
                options.opt_by_name[option.name] = option
                options.set_opt(option.name, option.value)
                for alias in option.aliases:
                    options.opts.append(alias)
                    options.opt_by_name[alias.name] = alias
                    options.set_opt(alias.name, option.value)
                option.aliases = []
            # Otherwise it's an arg:
            else:
                options.args.append(arg)
        return options

    # From Options.parse_doc():
    def parse_options_doc(self, options: Options, line: str) -> Optional[Options]:
        m = None

        def add_arg(m):
            name = m[1].strip()
            options.arg_by_name[name] = m[2].strip()
            options.args.append(name)

        try:
            if m := re.match(r"^(-) +[\|] *(.*)", line):
                add_arg(m)
                return options
            if option := self.parse_option_doc(Option(**{}), line):
                options.opt_by_name[option.name] = option
                options.opts.append(option)
                for alias in option.aliases:
                    options.opt_aliases[alias.name] = alias
                return options
            if m := re.match(r"^([^\|]+)[\|] *(.*)", line):
                add_arg(m)
                return options
            return None
        # finally:
        #  pass
        except Exception as e:
            raise Exception(
                f"parse_docstring: could not parse : {line!r} : {e!r}"
            ) from e

    # Option

    def parse_option_arg(self, option: Option, arg: str) -> Optional[Option]:
        option.style = "arg"
        return self.parse_option_simple(option, arg)

    def parse_option_doc(self, option: Option, arg: str) -> Optional[Option]:
        option.style = "doc"
        aliases = []
        if m := re.match(r"^(?:.+  |)Default: +(.+?)\.$", arg):
            option.default = m[1].strip()
        if m := re.match(r"^([^\|]+?)  \|  (.*)", arg):
            arg, *aliases = re.split(r", ", m[1].strip())
            option.description = m[2].strip()
        if result := self.parse_option_simple(option, arg):
            option.aliases = [
                self.parse_option_alias(option, alias) for alias in aliases
            ]
        return result

    def parse_option_alias(self, option: Option, opt: str) -> Optional[Option]:
        alias = Option(**{})
        assert self.parse_option_simple(
            alias, opt
        ), "parse_option_alias: expected simple option"
        alias.style = option.style
        alias.kind = option.kind
        alias.description = option.description
        alias.default = option.default
        alias.alias_of = option.name
        return alias

    def parse_option_simple(self, option: Option, arg: str) -> Optional[Option]:
        def matched_long(kind, name, val):
            option.arg = arg
            option.kind, option.full, option.name, option.value = (
                kind,
                f"--{name}",
                name,
                val,
            )
            return option

        def matched_flag(opt, kind, name, val):
            option.arg = arg
            opt.kind, opt.full, opt.name, opt.value = kind, f"-{name}", name, val
            return opt

        def matched_flags(kind, flags, val):
            flags = [*flags]
            matched_flag(option, kind, flags.pop(0), val)
            for flag in flags:
                option.aliases.append(matched_flag(Option(), kind, flag, val))
            return option

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
