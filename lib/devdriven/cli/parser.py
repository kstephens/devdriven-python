from typing import Optional, List
import re
import argparse
from .descriptor import Descriptor, Example
from .command import Command
from .option import Option, make_option
from .options import Options  # , make_options
from .types import Argv
from ..util import set_from_match, unpad_lines, trim_list


class Parser:
    ##########################################
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
            elif option := self.parse_option_arg(make_option(), arg):
                command.set_opt(option.name, option.value)
                for alias in option.aliases:
                    command.set_opt(alias.name, option.value)
            else:
                command.args.append(arg)
        return command

    ##########################################
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
            elif option := self.parse_option_arg(make_option(), arg):
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

    ##########################################
    # From Options.parse_doc():

    def parse_options_docstring(self, options: Options, line: str) -> Optional[Options]:
        m = None

        def add_arg(m):
            name = m[1].strip()
            options.arg_by_name[name] = m[2].strip()
            options.args.append(name)

        try:
            if m := re.match(r"^(-) +[\|] *(.*)", line):
                add_arg(m)
                return options
            if option := self.parse_option_doc(make_option(), line):
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

    ##########################################
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

    ##########################################
    # From Decriptor.parse_docstring()

    def parse_descriptor_docstring(self, desc: Descriptor, docstr: str) -> Descriptor:
        desc.options = Options(**{})
        found_aliases = False
        # debug = False
        lines = trim_list(unpad_lines(re.sub(r"\\\n", "", docstr).splitlines()))
        comments = []
        while lines:
            line = lines.pop(0)
            # if debug:
            #   ic(line)
            m = None
            if m := re.match(
                r"(?i)^:(?P<name>[-_a-z][-_a-z0-9]+)[:=] *(?P<value>.*)", line
            ):
                desc.metadata[m["name"]] = m["value"].strip()
            elif not desc.name and (
                m := re.match(
                    r"(?i)^(?P<name>[-_a-z][-_a-z0-9]+) +- +(?P<brief>.+)", line
                )
            ):
                set_from_match(desc, m)
            elif not found_aliases and (
                m := re.match(r"(?i)^Alias(?:es)?: +(.+)", line)
            ):
                desc.aliases.extend(re.split(r"\s*,\s*|\s+", m[1].strip()))
                found_aliases = True
            elif m := re.match(r"(?i)^(Arguments|Options|Examples):\s*$", line):
                pass
            elif m := re.match(r"^[#] (.+)", line):
                comments.append(m[1])
            elif m := re.match(r"^\$ (.+)", line):
                desc.examples.append(
                    Example(
                        command=m[1],
                        comments=comments,
                        output=None,
                    )
                )
                comments = []
            elif desc.options.parse_docstring(line):
                # if debug:
                #   ic((self.name, self.options))
                # pylint: disable-next=pointless-statement
                pass
            else:
                desc.detail.append(line)
            # if debug:
            #   ic(m and m.groupdict())
        desc.build_synopsis()
        desc.detail = trim_list(desc.detail)
        return desc

    ##########################################

    def argument_parser(self, desc: Descriptor) -> argparse.ArgumentParser:
        options = desc.options
        assert isinstance(options, Options)
        epilog: List[str] = []
        if desc.detail:
            epilog.extend(("  Details:", ""))
            epilog.extend(desc.detail)
        if desc.examples:
            epilog.extend(("", "  Examples:", ""))
            for example in desc.examples:
                epilog.extend([f"# {c}" for c in example.comments])
                epilog.append(f"$ {example.command}")
                if example.output:
                    epilog.extend(example.output)  # ???: is it a list or str
                epilog.append("")

        usage = desc.command_path()
        if options.opts:
            usage += ["[options]"]
        if options.args:
            usage += ["[arguments]"]

        parser = argparse.ArgumentParser(
            prog=desc.name,
            usage=" ".join(usage),
            description=desc.brief,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="\n".join(epilog),
        )

        for arg in options.args:
            name, default = arg, None
            # if args.optional:  # ...
            if m := re.match(r"^\[(.+)\]$", arg):
                name, default = m[1], ""  # ???
            parser.add_argument(name, default=default)
        for option in options.opts:
            args, kwargs = [], {}
            if option.aliases:
                args = [option.aliases[0].full, option.full]
            else:
                args = [option.full]
            if option.default is not None:
                kwargs["default"] = option.default
            if option.description:
                kwargs["help"] = option.description
            if option.kind == "flag":
                kwargs["action"] = (
                    "store_true" if option.value is True else "store_false"
                )
            parser.add_argument(*args, **kwargs)  # type: ignore  # arg-type
        return parser
