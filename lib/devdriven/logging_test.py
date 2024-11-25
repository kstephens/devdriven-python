from datetime import datetime, timezone
from logging import LogRecord
import re
import pytest
from devdriven.logging import JsonFormatter, numeric_level


def test_numeric_level():
    assert numeric_level("DEBUG") == 10
    assert numeric_level(10) == 10
    assert numeric_level(-1) == -1


def test_json_formatter():
    message_data = {"a": 1, "b": "str"}
    arg_data = {
        "rx": re.compile(r"foo/bar.*"),
        "now": datetime.fromtimestamp(123.456 * 2, tz=timezone.utc),
    }
    assert_message(["MESSAGE"], '"message":"MESSAGE","DATA_KEY":{}')
    with pytest.raises(Exception) as _e_info:
        assert_message(["MESSAGE -> %s %d"], '"message":"MESSAGE","DATA_KEY":{}')
    assert_message(
        ["MESSAGE", "arg1", 2], '"message":"MESSAGE | arg1 | 2","DATA_KEY":{}'
    )
    assert_message(
        ["MESSAGE -> %s %d", "arg1", 2], '"message":"MESSAGE -> arg1 2","DATA_KEY":{}'
    )
    assert_message(
        ["MESSAGE -> %s %d", "arg1", arg_data, 4],
        "".join(
            [
                '"message":"MESSAGE -> arg1 4",',
                '"DATA_KEY":{"rx":"re.compile(\'foo/bar.*\')",',
                '"now":"1970-01-01 00:04:06.912000+0000"}',
            ]
        ),
    )
    assert_message([message_data], '"message":"","DATA_KEY":{"a":1,"b":"str"}')
    assert_message(
        [message_data, "arg1", 2], '"message":"arg1 | 2","DATA_KEY":{"a":1,"b":"str"}'
    )
    assert_message(
        [message_data, "arg1", 2, arg_data, 4],
        "".join(
            [
                '"message":"arg1 | 2 | 4",',
                '"DATA_KEY":{"a":1,"b":"str","rx":"re.compile(\'foo/bar.*\')",',
                '"now":"1970-01-01 00:04:06.912000+0000"}',
            ]
        ),
    )


def assert_message(args, expected):
    result = 'MESSAGE_PREFIX: {'
    result += '"level":"DEBUG","timestamp":123.456,"pid":789,"thread":"MainThread",'
    result += expected
    result += ',"program":"TEST"}'
    assert format_message(*args) == expected


def format_message(msg, *args):
    options = {
        "message_prefix": "MESSAGE_PREFIX: ",
        "static_data": {"program": "TEST"},
        "data_key": "DATA_KEY",
    }
    formatter = JsonFormatter(**options)
    exc_info = None
    level = numeric_level("DEBUG")
    record = LogRecord(
        "NAME", level, "PATHNAME", -1, msg, args, exc_info, func="FUNC", sinfo="SINFO"
    )
    record.created = 123.456  # time.time() epoch sec
    record.process = 789
    return formatter.format(record)
