import time
from unittest.mock import Mock, call

import pytest

from . import timing as sut


def test_timing():
    def f(x):
        assert x
        time.sleep(x)
        return 3

    result, sec = sut.timing(f)(0.05)
    assert result == 3
    assert sec >= 0.05

    assert sut.capture_exception(f)(0.05) == (3, None)

    result, exc = sut.capture_exception(f)(0)
    assert result is None
    assert isinstance(exc, AssertionError)

    assert sut.with_timing_log(f)(0.05) == 3
    with pytest.raises(AssertionError):
        assert sut.with_timing_log(f)(0) == 3


def test_watch():
    def f(x, y=None):
        assert (x, y) == (2, 3)
        if f_mock.call_count == 4:
            raise KeyboardInterrupt("test_watch")
        return f_mock.call_count

    def make_mock():
        mock = Mock()
        mock.side_effect = f
        mock.__name__ = f.__name__
        return mock

    def log_msg(msg):
        assert "### watch :  " in msg
        assert ": f : " in msg

    def log_result(x):
        assert isinstance(x, int)

    options = {"wait": 0.01, "log_msg": log_msg, "log_result": log_result}
    f_mock = make_mock()
    assert sut.watch(f_mock, n=3, **options)(2, y=3) == 3
    f_mock.assert_called_with(2, y=3)

    # counted = count_calls(f)
    # assert sut.watch(counted, n=3, **options)(2, y=3) == 3
    # assert counted._calls == 3

    f_mock = make_mock()
    with pytest.raises(KeyboardInterrupt):
        sut.watch(f_mock, n=5, **options)(2, y=3)
    assert(f_mock.call_count) == 4


def count_calls(f):
    "Combinator: returns a function g, that increment g._calls."

    def counted(*args, **kwargs):
        counted._calls += 1
        return f(*args, **kwargs)

    counted._calls, counted.__name__, counted.__qualname__ = (
        0,
        f.__name__,
        f.__qualname__,
    )
    return counted
