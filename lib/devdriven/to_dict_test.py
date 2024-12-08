import re
import subprocess
from datetime import datetime, timezone
from dataclasses import dataclass
import pytest
from . import to_dict


def test_walk():
    fut = to_dict.to_dict
    assert fut(None) is None
    assert fut(123) == 123
    assert fut(123.45) == 123.45
    assert fut("abc") == "abc"
    assert fut(b"xyz") == "<BYTES[3]:xyz>"
    assert fut(b"\xffqwerty") == "<BYTES[7]>"
    assert fut("🤷".encode("utf-8")) == "<BYTES[4]:🤷>"
    assert fut([123, b"xyz"]) == [123, "<BYTES[3]:xyz>"]
    assert fut({"a": b"xyz", "b": 123, "c": b"wsad"}) == {
        "a": "<BYTES[3]:xyz>",
        "b": 123,
        "c": "<BYTES[4]:wsad>",
    }
    assert fut(re.compile(r"^rx", re.IGNORECASE)) == "re.compile('^rx', re.IGNORECASE)"
    actual = fut(datetime.fromtimestamp(1699571701.203033, tz=timezone.utc))
    assert actual == "2023-11-09 23:15:01.203033+0000"
    assert fut(Exception("E")) == {"class": "Exception", "message": "E"}
    other = to_dict.ToDict()
    assert fut(other)["class"] == "ToDict"
    fut = to_dict.ToDict()
    assert fut(None) is None


def test_dump_json():
    fut = to_dict.dump_json
    actual = fut({"a": b"xyz", "b": 123, "c": b"wsad"}, 2)
    expected = '{\n  "a": "<BYTES[3]:xyz>",\n  "b": 123,\n  "c": "<BYTES[4]:wsad>"\n}'
    assert actual == expected


def test_walk_oserror():
    fut = to_dict.to_dict
    with pytest.raises(OSError) as exc_info:
        read_file("Does-Not-Exist")
    assert fut(exc_info.value) == {
        "class": "FileNotFoundError",
        "message": "[Errno 2] No such file or directory: 'Does-Not-Exist'",
        "errno": 2,
        "strerror": "No such file or directory",
        "filename": "Does-Not-Exist",
        "filename2": None,
    }


def read_file(name):
    with open(name, "rb") as file:
        return file.read()


def test_walk_subprocess():
    fut = to_dict.to_dict
    result = subprocess.run(["/bin/echo", "OK"], check=True, capture_output=True)
    assert fut(result) == {
        "args": ["/bin/echo", "OK"],
        "returncode": 0,
        "stdout": "<BYTES[3]:OK\n>",
        "stderr": "<BYTES[0]>",
    }


def test_walk_subprocess_error():
    fut = to_dict.to_dict
    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        subprocess.run(["false"], check=True)
    assert fut(exc_info.value) == {
        "class": "CalledProcessError",
        "message": "Command '['false']' returned non-zero exit status 1.",
        "returncode": 1,
        "stdout": None,
        "stderr": None,
    }


def test_walk_dataclass():
    fut = to_dict.to_dict
    assert fut(ExampleDataclass("foo", 123)) == {
        "class": "<class 'devdriven.to_dict_test.ExampleDataclass'>",
        "fields": {
            "name": "foo",
            "value": 123,
        },
    }


@dataclass
class ExampleDataclass:
    name: str
    value: int
