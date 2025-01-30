from dataclasses import asdict
from . import Option


def test_parse_doc_long_value():
    obj = Option().parse_doc("--opt=STRING  |  desc.")
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


def test_parse_doc_long_flag():
    obj = Option().parse_doc("--opt  |  desc.")
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


def test_parse_doc_long_flag_default():
    obj = Option().parse_doc("--opt  |  desc.  Default: True.")
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


def test_parse_doc_long_flag_false():
    obj = Option().parse_doc("++opt  |  desc.")
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


def test_parse_doc_alias_flag():
    obj = Option().parse_doc("--opt, -o  |  opt: doc")
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


def test_parse_doc_long_opt():
    obj = Option().parse_doc("--opt  |  desc.")
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


def test_parse_doc_long_opt_default():
    obj = Option().parse_doc("--opt  |  desc.  Default: True.")
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


def test_parse_doc_long_opt_false():
    obj = Option().parse_doc("++opt  |  desc.")
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


def test_parse_doc_alias_opt():
    obj = Option().parse_doc("--opt, -o  |  opt: doc")
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
