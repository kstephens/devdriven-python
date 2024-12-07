from dataclasses import asdict
from . import parser as sut
from .command import Command
from .option import Option
from .options import Options

def parse_option_doc(line: str) -> Option:
    return sut.Parser().parse_option_doc(Option(), "--opt=STRING  |  desc.")

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


def xtest_parse_option_doc_long_flag_default():
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


def xtest_parse_option_doc_long_flag_false():
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


def xtest_parse_option_doc_alias_flag():
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


def xtest_parse_option_doc_long_opt():
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


def xtest_parse_option_doc_long_opt_default():
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


def xtest_parse_option_doc_long_opt_false():
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


def xtest_parse_option_doc_alias_opt():
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
