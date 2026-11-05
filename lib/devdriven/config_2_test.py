import os
from pathlib import Path

import pytest

from . import config_2 as sut

CONFIG_DIR = "tests/data/config"


def test_config_file():
    variables = {
        "TEST_ENVIRON_SET": "TEST_ENVIRON_SET",
        "TEST_ENVIRON_DELETE_ME": "123",
    }
    assert list(sut.config_file("tests/data/config/test.yml", variables).keys()) == [
        "a",
        "b",
    ]


def test_merge_configs():
    assert sut.merge(
        [
            {"a": 2, "b": 3},
            {"a": 5, "d": 7},
        ]
    ) == {"a": 5, "b": 3, "d": 7}


def test_read_revision_missing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(sut, "ROOT_DIR", tmp_path)
    assert sut.read_revision() == "unknown"


def test_read_revision_present_file(monkeypatch, tmp_path):
    monkeypatch.setattr(sut, "ROOT_DIR", tmp_path)
    (tmp_path / "REVISION").write_text("abc123def456\n", encoding="utf-8")
    assert sut.read_revision() == "abc123def456"


def test_read_revision_blank_file(monkeypatch, tmp_path):
    monkeypatch.setattr(sut, "ROOT_DIR", tmp_path)
    (tmp_path / "REVISION").write_text("   \n", encoding="utf-8")
    assert sut.read_revision() == "unknown"


def test_replace_variables():
    config = {
        "a": "<<${VAR}>>",
        "b": 3,
    }
    variables = {"VAR": "VAL"}
    assert sut.replace_variables(variables, config) == {
        "a": "<<VAL>>",
        "b": 3,
    }


def test_options_config():
    assert sut.options_config(
        {
            "a": 2,
            ".b.c.d": 3,
        }
    ) == ({"a": 2}, {"b": {"c": {"d": 3}}})


def test_load_config():
    os.environ["TEST_ENVIRON_SET"] = "TEST_ENVIRON_SET"
    os.environ["TEST_ENVIRON_DELETE_ME"] = "123"

    env = "test"
    argv = [
        "--option-a=2",
        "--c.d=argv-option",
        "--flag",
        "--.c.d=.c.d-override",
        "--.e=.e-override",
        "argument",
    ]
    actual = sut.load_config(env=env, argv=argv, config_dir=CONFIG_DIR)
    assert actual == {
        "main": {
            "env": env,
            "argv": {
                "argv": argv,
                "args": ["argument"],
                "opts": {
                    "option_a": "2",
                    "c.d": "argv-option",
                    "flag": True,
                },
                "overrides": {
                    "c": {
                        "d": ".c.d-override",
                    },
                    "e": ".e-override",
                },
            },
            "config_dir": CONFIG_DIR,
            "config_files": [
                str(Path(f"{CONFIG_DIR}/{file}").resolve())
                for file in ("default.yml", "test.yml")
            ],
        },
        "a": [
            {
                "name": "foo",
                "x": 1,
                "y": "234",
                "set_environ": "| TEST_ENVIRON_SET |",
                "unset_environ": "|  |",
                "not_environ": "| $NOT_ENVIRON |",
            },
        ],
        "b": "override",
        "c": {"d": ".c.d-override"},
        "environ": {
            "TEST_ENVIRON": 123,
            "TEST_ENVIRON_DELETE_ME": None,
        },
        "e": ".e-override",
    }

    assert os.environ["TEST_ENVIRON"] == "123"
    assert "TEST_ENVIRON_DELETE_ME" not in os.environ

    argv = argv + ["--env=test"]
    actual = sut.load_config(argv=argv, config_dir=CONFIG_DIR, env_prefix="_IGNORE_")
    assert set(actual["main"]["argv"]["opts"].keys()) == {
        "option_a",
        "c.d",
        "env",
        "flag",
    }
    assert set(actual.keys()) == {
        "a",
        "b",
        "c",
        "e",
        "environ",
        "main",
    }

    os.environ.pop("TEST_ENVIRON_SET")
    assert os.environ.pop("TEST_ENVIRON_DELETE_ME", None) is None


def test_load_config_override_environ():
    os.environ["TEST_ENV"] = "INVALID"
    argv = []
    actual = sut.load_config(
        argv=argv,
        config_dir=CONFIG_DIR,
        env_prefix="TEST_",
        environ={"TEST_ENV": "test"},
    )
    assert actual["main"]["env"] == "test"
    os.environ.pop("TEST_ENV")


def test_load_config_empty_environ():
    os.environ["TEST_ENV"] = "INVALID"
    argv = []
    with pytest.raises(FileNotFoundError, match=r"data/config/local.yml"):
        sut.load_config(
            argv=argv, config_dir=CONFIG_DIR, env_prefix="TEST_", environ={}
        )
    os.environ.pop("TEST_ENV")


def test_main():
    os.environ["TEST_ENVIRON_SET"] = "TEST_ENVIRON_SET"
    os.environ["TEST_ENVIRON_DELETE_ME"] = "123"
    assert sut.main(["--config-dir=tests/data/config", "--env=test"]) == 0
    os.environ.pop("TEST_ENVIRON_SET")
    assert os.environ.pop("TEST_ENVIRON_DELETE_ME", None) is None
