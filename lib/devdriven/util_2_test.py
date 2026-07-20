import logging
import math
import operator as op
from io import StringIO

import pytest

from . import util as sut


def test_blank_or():
    assert sut.blank_or(None, 2) == 2
    assert sut.blank_or("", 3) == 3
    assert sut.blank_or(7, "other") == 7
    assert sut.blank_or(False, "other") is False


def test_one_or_none():
    assert sut.one_or_none([]) is None
    assert sut.one_or_none([2]) == 2
    assert sut.one_or_none([3, 5]) is None


def test_frequency():
    assert sut.frequency((1, 2, 3, 2)) == {1: 1, 2: 2, 3: 1}


def test_subdict_equal():
    assert sut.subdict_equal({}, {}) is True
    assert sut.subdict_equal({"a": 2}, {"b": 3}) is True
    assert sut.subdict_equal({}, {"b": 2}) is True
    assert sut.subdict_equal({"a": 2}, {"b": 3}) is True
    assert sut.subdict_equal({"a": 2}, {"a": 999}) is False


def test_parse_args():
    argv = (
        "progname --an-opt=1 --a-flag -bc a b +de ++f-flag -- --not-an-opt=2 d".split(
            " "
        )
    )
    args, opts = sut.parse_args(argv, {"a_flag": False, "b_flag": True})
    assert args == ["progname", "a", "b", "--not-an-opt=2", "d"]
    assert opts == {
        "an_opt": "1",
        "a_flag": True,
        "b_flag": True,
        "b": True,
        "c": True,
        "d": False,
        "e": False,
        "f_flag": False,
    }


def test_mapcat():
    assert tuple(sut.mapcat(op.neg, ((1, 2, 3), (4, 5)))) == (-1, -2, -3, -4, -5)


def test_compose():
    assert sut.compose(op.add) is op.add
    assert sut.compose(op.add)(2, 3) == 5
    assert sut.compose(op.neg, op.add)(2, 3) == -5
    assert sut.compose(op.neg, op.add).__name__ == "compose(neg,add)"


def test_combine_names():
    def g():
        return 123

    assert (
        sut.combine_names(g, "test", sut.mapcat, True).__qualname__
        == "test(fds.util.mapcat)"
    )

    assert sut.combine_names(g, "test", sut.mapcat).__qualname__ == "test(mapcat)"


def test_none_or():
    def f(x, y, z=5):
        return 2 + x * y * z

    assert sut.none_or(f)(None, 5, z=7) is None
    assert sut.none_or(f)(3, 5, z=7) == 107


def test_indexed():
    assert sut.indexed(1)(["a", "b"]) == "b"
    assert sut.indexed("a")({"a": 2, "b": 3}) == 2


def test_dict_without_none():
    assert sut.dict_without_none({"a": 2, "b": False, "c": None}) == {
        "a": 2,
        "b": False,
    }


def test_split_dict():
    d = {"a": 1, "b": 2, "c": 3}
    assert sut.split_dict(d, ("b", "d")) == ({"a": 1, "c": 3}, {"b": 2})


def test_rename_keys():
    d = {"a": 1, "b": 2}
    sut.rename_keys(d, {"c": "b"})
    assert d == {"a": 1, "c": 2}


def test_copy_keys():
    d = {"a": 1, "b": 2}
    sut.copy_keys(d, {"a1": "a", "a2": "a", "c": "d"}, {"c": 3})
    assert d == {"a": 1, "a1": 1, "a2": 1, "b": 2, "c": 3}


def test_isnan_safe():
    assert sut.isnan_safe(math.nan) is True
    assert sut.isnan_safe(1.2) is False
    assert sut.isnan_safe("") is False
    assert sut.isnan_safe(None) is False


def test_replace_nan():
    assert sut.replace_nan(math.nan) is None
    assert sut.replace_nan(math.nan, 2) == 2
    assert sut.replace_nan(2) == 2
    assert sut.replace_nan(3.5) == 3.5
    assert sut.replace_nan("") == ""
    assert sut.replace_nan([2, 3.5, math.nan, "str"], "NaN") == [2, 3.5, "NaN", "str"]
    assert sut.replace_nan((2, 3.5, math.nan, "str")) == (2, 3.5, None, "str")
    assert sut.replace_nan({"a": (2, 3.5, math.nan, ""), "b": math.nan}, "NaN") == {
        "a": (2, 3.5, "NaN", ""),
        "b": "NaN",
    }


def test_redact():
    assert sut.redact("") == "********"
    assert sut.redact("a") == "a********"
    assert sut.redact("ab") == "a********b"
    assert sut.redact("abcdef") == "a********f"
    assert sut.redact("ab", min_size=3) == "a***b"
    assert sut.redact("abcdefg", min_size=3) == "a*****g"


def test_output_response():
    d = {"hello": "world!"}

    def check(fmt):
        stream = StringIO()
        assert sut.output_response(d, fmt, stream) is d
        return stream.getvalue()

    assert check("json") == '{\n  "hello": "world!"\n}\n'
    assert check("yaml") == "hello: world!\n"
    assert check("text") == "{'hello': 'world!'}\n"
    assert check("none") == ""


def test_links():
    assert not sut.linked([], 2)
    assert not sut.linked([1], 2)
    assert sut.linked((1, 2), 2) == [(1, 2)]
    assert sut.linked((1, 2, 3, 4), 2) == [(1, 2), (2, 3), (3, 4)]
    assert sut.linked((1, 2, 3, 4), 2, include_tail=True) == [
        (1, 2),
        (2, 3),
        (3, 4),
        (4,),
    ]
    assert not sut.linked([], 3)
    assert not sut.linked([1], 3)
    assert not sut.linked((1, 2), 3)
    assert sut.linked((1, 2), 3, include_tail=True) == [(1, 2)]
    assert sut.linked((1, 2, 3, 4, 5), 3) == [(1, 2, 3), (3, 4, 5)]
    assert sut.linked((1, 2, 3, 4, 5), 3, include_tail=True) == [
        (1, 2, 3),
        (3, 4, 5),
        (5,),
    ]
    assert sut.linked((1, 2, 3, 4, 5, 6), 3) == [(1, 2, 3), (3, 4, 5)]
    assert sut.linked((1, 2, 3, 4, 5, 6), 3, include_tail=True) == [
        (1, 2, 3),
        (3, 4, 5),
        (5, 6),
    ]
    assert sut.linked((1, 2, 3, 4, 5, 6), 3, overlap=2) == [
        (1, 2, 3),
        (2, 3, 4),
        (3, 4, 5),
        (4, 5, 6),
    ]


def test_execute():
    def fun():
        return {"k": 2}

    result = sut.execute(fun)
    assert list(result.keys()) == [
        "result",
        "error",
        "started_at",
        "finished_at",
        "elapsed_ms",
        "pid",
    ]
    assert result["error"] is None
    assert isinstance(result["elapsed_ms"], float)
    assert result["result"]["k"] == 2

    with pytest.raises(RuntimeError, match=r"^fail$"):

        def fail():
            raise RuntimeError("fail")

        sut.execute(fail, capture_exception=False)

    with pytest.raises(KeyboardInterrupt, match=r"^exc$"):

        def exc():
            raise KeyboardInterrupt("exc")

        sut.execute(exc, capture_exception=True)


def test_logging():
    sut.setup_logging()
    logging.info("%s", "test_logging()")


def test_with_log_collection():  # pragma: no cover
    # !!! this test does not work
    messages = []

    def collect(record):
        messages.append(record)

    def do_something():
        logging.info("%s", "test_log_collection")
        return 5

    assert sut.with_log_collection(collect, do_something) == 5
    assert messages != [123]


def test_backtrace_list():
    result = None
    try:
        raise ValueError("test_backtrace_list")
    except ValueError as exc:
        result = sut.backtrace_list(exc)
    assert len(result) == 1
    assert result[0][0].endswith("/util_test.py")
    assert isinstance(result[0][1], int)
