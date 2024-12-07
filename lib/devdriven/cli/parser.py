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
    def parse_options_argv(self, options: Options, argv: Argv):
        options.argv = argv.copy()
        options.args = []
        while argv:
            arg = argv.pop(0)
            if arg == "--":
                options.args.extend(argv)
                break
            if options.args:
                options.args.append(arg)
            elif option := self.parse_option_arg(Option(**{}), arg):
                options.opts.append(option)
                options.opt_by_name[option.name] = option
                options.set_opt(option.name, option.value)
                for alias in option.aliases:
                    options.opts.append(alias)
                    options.opt_by_name[alias.name] = alias
                    options.set_opt(alias.name, option.value)
                option.aliases = []
            else:
                options.args.append(arg)


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
            option.aliases = [self.parse_option_alias(option, alias) for alias in aliases]
        return result

    def parse_option_alias(self, option: Option, opt: str) -> Optional[Option]:
        alias = Option(**{})
        assert self.parse_option_simple(alias, opt), "parse_option_alias: expected simple option"
        alias.style = option.style
        alias.kind = option.kind
        alias.description = option.description
        alias.default = option.default
        alias.alias_of = option.name
        return alias

    def parse_option_simple(self, option: Option, arg: str) -> Optional[Option]:
        def matched(kind: str, name: str, full: str, value: Any) -> Option:
            option.arg, option.kind, option.name, option.full, option.value = arg, kind, name, full, value
            return option
        def matched_option(name: str, val: Any) -> Option:
            return matched("option", name, f"--{name}", val)
        def matched_flag(name: str, val: Any) -> Option:
            return matched("flag", name, f"-{name}", val)
        if m := re.match(r"^--([a-zA-Z][-_a-zA-Z0-9]*)=(.*)$", arg):
            return matched_option(m[1], m[2])
        if m := re.match(r"^--no-([a-zA-Z][-_a-zA-Z0-9]+)$", arg):
            return matched_flag(m[1], False)
        if m := re.match(r"^-(-([a-zA-Z][-_a-zA-Z0-9]+))$", arg):
            return matched_flag(m[1], True)
        if m := re.match(r"^\+\+([a-zA-Z][-_a-zA-Z0-9]+)$", arg):
            return matched_flag(m[1], False)
        if m := re.match(r"^-([a-zA-Z][-_a-zA-Z0-9]*)$", arg):
            return matched_flag(m[1], True)
        if m := re.match(r"^\+([a-zA-Z][-_a-zA-Z0-9]*)$", arg):
            return matched_flag(m[1], False)
        return None

