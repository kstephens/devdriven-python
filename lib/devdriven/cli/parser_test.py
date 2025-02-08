from typing import List, Tuple
from dataclasses import asdict
from . import parser as sut
from ..util import slice_keys
from .descriptor import Descriptor
from .command import Command
from .option import Option
from .options import Options


##########################################


def parse_descriptor_docstring(docstr: str) -> Tuple[sut.Parser, Descriptor]:
    parser = sut.Parser()
    desc = Descriptor(**{})
    return parser, parser.parse_descriptor_docstring(desc, docstr)


def test_parse_descriptor_docstring():
    docstr = """
  NAME-lower_0 -  BRIEF DESCRIPTION.

  Aliases: ALIAS-1, ALIAS-2

  ARG-1,... [ARG-2,...] [ARG-3,...]    |  COLs to summarize STATs grouped by GROUP-BY

  ARG-1,...       |  Any numeric columns separated by ",".
  ARG-2,...       |  One or more of: 'a', 'b'.\
  See Blah.  Default: ALL.
  ARG-3,...       |  Any column not in the COL list.  Default: is all of them.

  --simple, -S         |  Simple format.
  --title=NAME         |  Set `<title>` and add a `<div>` at the top.

Some detail:
  This line.
  That line...  \
  Continued

  :suffixes: .S1,.S2

  Examples:

# Does x
# and y:
$ command-1 x y z
$ command-2 a b c

"""
    parser, desc = parse_descriptor_docstring(docstr)
    actual = vars(desc).copy()  # | asdict(desc)
    expected = {
        "name": "NAME-lower_0",
        "brief": "BRIEF DESCRIPTION.",
        "aliases": ["ALIAS-1", "ALIAS-2"],
        "detail": [
            "Some detail:",
            "This line.",
            "That line...    Continued",
        ],
        "section": "",
        "metadata": {"suffixes": ".S1,.S2"},
        "synopsis": "NAME-lower_0 [--simple] [--title=NAME] [ARG-1,... [ARG-2,...] "
        "[ARG-3,...]] [ARG-1,...] [ARG-2,...] [ARG-3,...]",
        "synopsis_prefix": [],
        "examples": [
            {
                "command": "command-1 x y z",
                "comments": ["Does x", "and y:"],
                "output": None,
            },
            {
                "command": "command-2 a b c",
                "comments": [],
                "output": None,
            },
        ],
    }

    actual["examples"] = [asdict(ex) for ex in actual["examples"]]
    assert slice_keys(actual, expected.keys()) == expected

    expected = {
        "args": [
            "ARG-1,... [ARG-2,...] [ARG-3,...]",
            "ARG-1,...",
            "ARG-2,...",
            "ARG-3,...",
        ],
    }

    actual["options"] = asdict(actual["options"])
    assert slice_keys(actual["options"], expected.keys()) == expected
    print("")

    actual = parser.argument_parser(desc).format_help()
    expected = """
usage: NAME-lower_0 [options] [arguments]

BRIEF DESCRIPTION.

positional arguments:
  ARG-1,... [ARG-2,...] [ARG-3,...]
  ARG-1,...
  ARG-2,...
  ARG-3,...

options:
  -h, --help            show this help message and exit
  -S, --simple          Simple format.
  --title TITLE         Set `<title>` and add a `<div>` at the top.

details:
  Some detail:
  This line.
  That line...    Continued

examples:
  # Does x
  # and y:
  $ command-1 x y z

  $ command-2 a b c
"""
    assert actual == expected[1:]


##########################################


def parse_command_argv(argv: List[str]) -> Options | None:
    return sut.Parser().parse_command_argv(Command(**{}), argv.copy())


def test_parse_command_argv():
    argv = ["-abc", "--flag1", "++flag2", "--no-flag3", "--opt=g", "h", "i", "-j"]
    obj = parse_command_argv(argv)
    assert obj.argv == argv
    assert obj.args == ["h", "i", "-j"]
    assert obj.opts == {
        "a": True,
        "b": True,
        "c": True,
        "flag1": True,
        "flag2": False,
        "flag3": False,
        "opt": "g",
    }
    assert not obj.opts_defaults
    assert not obj.opt_char_map
    assert obj.rtn is None


##########################################


def parse_options_argv(argv: List[str]) -> Options | None:
    return sut.Parser().parse_options_argv(Options(**{}), argv.copy())


def test_parse_options_argv():
    argv = ["-abc", "--flag", "--opt=g", "h", "i", "-j"]
    obj = parse_options_argv(argv)
    assert obj.argv == argv
    assert [o.name for o in obj.opts] == ["a", "b", "c", "flag", "opt"]
    assert [o.value for o in obj.opts] == [True, True, True, True, "g"]
    assert obj.args == ["h", "i", "-j"]


def test_parse_options_argv_dash():
    argv = ["-abc", "--flag", "--", "--opt=g", "h", "i", "-j"]
    obj = parse_options_argv(argv)
    assert obj.opt("a") is True
    assert obj.opt("a", 2) is True
    assert obj.opt("b", 3) is True
    assert obj.opt("c", 5) is True
    assert obj.opt("flag", 7) is True
    assert list(map(lambda o: o.name, obj.opts)) == ["a", "b", "c", "flag"]
    assert list(map(lambda o: o.value, obj.opts)) == [
        True,
        True,
        True,
        True,
    ]
    assert obj.args == ["--opt=g", "h", "i", "-j"]


def test_parse_options_argv_dash_in_args():
    argv = ["-abc", "--flag", "--opt=g", "h", "i", "-j"]
    obj = parse_options_argv(argv)
    assert obj.args == ["h", "i", "-j"]
    assert obj.opt("a", 2) is True
    assert obj.opt("b", 3) is True
    assert obj.opt("c", 3) is True
    assert obj.opt("opt", 5) == "g"
    assert obj.opt("x", 7) == 7
    assert obj.opt("j", 11) == 11


##########################################


def parse_option_doc(line: str) -> Option | None:
    return sut.Parser().parse_option_doc(Option(**{}), line)


def test_parse_option_doc_long_value():
    obj = parse_option_doc("--opt=STRING  |  desc.")
    assert asdict(obj) == {
        "aliases": [],
        "arg": "--opt=STRING",
        "default": None,
        "description": "desc.",
        "full": "--opt",
        "kind": "option",
        "name": "opt",
        "style": "doc",
        "value": "STRING",
        "alias_of": None,
    }


def test_parse_option_doc_long_flag():
    obj = parse_option_doc("--opt  |  desc.")
    assert asdict(obj) == {
        "aliases": [],
        "arg": "--opt",
        "default": None,
        "description": "desc.",
        "full": "--opt",
        "kind": "flag",
        "name": "opt",
        "style": "doc",
        "value": True,
        "alias_of": None,
    }


def test_parse_option_doc_long_flag_default():
    obj = parse_option_doc("--opt  |  desc.  Default: True.")
    assert asdict(obj) == {
        "aliases": [],
        "arg": "--opt",
        "default": "True",
        "description": "desc.  Default: True.",
        "full": "--opt",
        "kind": "flag",
        "name": "opt",
        "style": "doc",
        "value": True,
        "alias_of": None,
    }


def test_parse_option_doc_long_flag_false():
    obj = parse_option_doc("++opt  |  desc.")
    assert asdict(obj) == {
        "aliases": [],
        "arg": "++opt",
        "default": None,
        "description": "desc.",
        "full": "--opt",
        "kind": "flag",
        "name": "opt",
        "style": "doc",
        "value": False,
        "alias_of": None,
    }


def test_parse_option_doc_alias_flag():
    obj = parse_option_doc("--opt, -o  |  opt: doc")
    assert asdict(obj) == {
        "aliases": [
            {
                "aliases": [],
                "arg": "-o",
                "default": None,
                "description": "opt: doc",
                "full": "-o",
                "kind": "flag",
                "name": "o",
                "style": "doc",
                "value": True,
                "alias_of": "opt",
            }
        ],
        "arg": "--opt",
        "default": None,
        "description": "opt: doc",
        "full": "--opt",
        "kind": "flag",
        "name": "opt",
        "style": "doc",
        "value": True,
        "alias_of": None,
    }


def test_parse_option_doc_long_opt():
    obj = parse_option_doc("--opt  |  desc.")
    assert asdict(obj) == {
        "aliases": [],
        "arg": "--opt",
        "default": None,
        "description": "desc.",
        "full": "--opt",
        "kind": "flag",
        "name": "opt",
        "style": "doc",
        "value": True,
        "alias_of": None,
    }


def test_parse_option_doc_long_opt_default():
    obj = parse_option_doc("--opt  |  desc.  Default: True.")
    assert asdict(obj) == {
        "aliases": [],
        "arg": "--opt",
        "default": "True",
        "description": "desc.  Default: True.",
        "full": "--opt",
        "kind": "flag",
        "name": "opt",
        "style": "doc",
        "value": True,
        "alias_of": None,
    }


def test_parse_option_doc_long_opt_false():
    obj = parse_option_doc("++opt  |  desc.")
    assert asdict(obj) == {
        "aliases": [],
        "arg": "++opt",
        "default": None,
        "description": "desc.",
        "full": "--opt",
        "kind": "flag",
        "name": "opt",
        "style": "doc",
        "value": False,
        "alias_of": None,
    }


def test_parse_option_doc_alias_opt():
    obj = parse_option_doc("--opt, -o  |  opt: doc")
    assert asdict(obj) == {
        "aliases": [
            {
                "aliases": [],
                "arg": "-o",
                "default": None,
                "description": "opt: doc",
                "full": "-o",
                "kind": "flag",
                "name": "o",
                "style": "doc",
                "value": True,
                "alias_of": "opt",
            }
        ],
        "arg": "--opt",
        "default": None,
        "description": "opt: doc",
        "full": "--opt",
        "kind": "flag",
        "name": "opt",
        "style": "doc",
        "value": True,
        "alias_of": None,
    }
