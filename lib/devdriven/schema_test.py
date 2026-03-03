import re
from typing import Any, Callable, Dict, List, Literal, Optional, Set, Tuple, Union
import pytest
from icecream import ic  # pylint: disable=unused-import
from . import schema as sut


obj = object()
NoneType = type(None)
MyDict = Dict[str, int]
MyUnion = sut.Union[int, {"a": int}]  # type: ignore


@pytest.mark.parametrize(
    "data, schema, expected",  # , *notes",
    (
        (object(), Any, True),
        (True, bool, True),
        (True, int, True),
        (True, float, False),
        (True, str, False),
        (2, bool, False),
        (2, int, True),
        (2, float, False),
        (2, str, False),
        (3.5, bool, False),
        (3.5, int, False),
        (3.5, float, True),
        (3.5, str, False),
        ("X", bool, False),
        ("X", int, False),
        ("X", float, False),
        ("X", str, True),
        (2, 2, True),
        (2, 3, False),
        (2, "X", False),
        ("X", 2, False),
        ("X", "X", True),
        ("X", "Y", False),
        ("X", str, True),
        ("X", int, False),
        ({}, dict, True),
        ("X", str, True),
        ([], [], True),
        ([], list, True),
        ([2], list, True),
        ([], List, True),
        ([2], List, True),
        ([2, "X"], List, True),
        ([], List[int], True),
        ([2], List[int], True),
        ([2, 3.5], List[int], False),
        (2, int | float, True),
        (3.5, int | float, True),
        ({}, {}, True),
        (False, {}, False),
        ({"a": "b"}, {"a": "b"}, True),
        ({"a": "b"}, 2, False),
        ({"a": 1}, {str: int}, True),
        ({"a": "b"}, {str: int}, False),
        ({"a": "b", 2: 3.5}, {"a": "b", int: float}, True),
        ({"a": "b", 2: 3.5}, {"a": "c", int: float}, False),
        ({"a": "b", 2: 3.5}, {int: float}, False),
        ({"a": [1, 2]}, {"a": List[int]}, True),
        ({"a": [1, 2.4]}, {"a": List[int]}, False),
        ({}, Dict[str, int], True),
        ({"a": 2}, Dict[str, int], True),
        ({"a": 2, "b": "X"}, Dict[str, int], False),
        ({"a": 2, 3: 4}, Dict[str, int], False),
        (tuple(), Tuple, True),
        ((1,), Tuple, True),
        (None, Tuple, False),
        ((1,), [1], False),
        ([1], [1, 2], False),
        ([1, 2, 3], [1, -1, 3], False),
        (2, int | float, True),
        (3.5, int | float, True),
        ("x", int | float, False),
        ((2,), Tuple[int], True),
        ("abc", re.compile(r"b"), True),
        ("abc", re.compile(r"x"), False),
        (2, lambda x: isinstance(x, int), True),
        (3.5, lambda x: isinstance(x, int), False),
        (obj, sut.Is[obj], True),
        (3, sut.Is[obj], False),
        (2, sut.Equal[2], True),
        (2.0, sut.Equal[2], True),
        (3.0, sut.Equal[2], False),
        (True, sut.TypeIs[bool], True),
        (True, bool, True),
        (True, sut.TypeIs[int], False),
        (True, int, True),
        (True, sut.TypeIs[object], False),
        (True, object, True),
        (2, Literal[2, 3], True),
        (3, Literal[2, 3], True),
        (5, Literal[2, 3], False),
        (None, MyDict, False),
        ({"a": 1}, MyDict, True),
        ({"a": "b"}, MyDict, False),
        (None, Tuple[int, float], False),
        ((2, 3.5), Tuple[int, float], True),
        ((2, "x"), Tuple[int, float], False),
        ((2, 3.5, 7), Tuple[int, ...], True),
        ((2,), Tuple[int, float], False),
        (None, Set[int], False),
        ({2, 3}, Set[int], True),
        ({2, "x"}, Set[int], False),
        (2, Union[int, Union[float, list]], True),
        (3.5, Union[int, Union[float, list]], True),
        ([], Union[int, Union[float, list]], True),
        (obj, Union[int, Union[float, list]], False),
        (2, MyUnion, True),
        ({"a": 3}, MyUnion, True),
        ({"a": 3, "b": 5}, MyUnion, False),
        ({}, MyUnion, False),
        ("", MyUnion, False),
        ({"a": "x"}, MyUnion, False),
        ((2, "s"), MyUnion | Tuple[int, str], True),
        ((2, "s"), Tuple[int, str] | MyUnion, True),
        (2, sut.Union[int], True),
        # {k: v, ...: VT}:
        ({"a": 1}, {"a": int, "b": int}, False),
        ({"a": 1, "b": 2}, {"a": int}, False),
        ({"a": 1}, {"a": int, ...: Any}, True),
        ({"a": 1, "b": 2}, {"a": int, ...: Any}, True),
        ({"a": 1, "b": 2}, {"a": int, ...: int}, True),
        ({"a": 1, "b": "x"}, {"a": int, ...: Any}, True),
        ({"a": 1, "b": "x"}, {"a": int, ...: int}, False),
        # {k: v, Optional: VT}:
        ({"a": 1}, {"a": int, Optional: Any}, True),
        ({"a": 1, "b": 2}, {"a": int, Optional: Any}, True),
        ({"a": 1, "b": 2}, {"a": int, Optional: int}, True),
        ({"a": 1, "b": "x"}, {"a": int, Optional: Any}, True),
        ({"a": 1, "b": "x"}, {"a": int, Optional: int}, False),
        # {k: v, Optional[KT], VT}:
        ({"a": 1}, {"a": int, Optional[int]: Any}, True),
        ({"a": 1, "b": 2}, {"a": int, Optional[int]: Any}, False),
        ({"a": 1, "b": 2}, {"a": int, Optional[int]: int}, False),
        ({"a": 1, "b": "x"}, {"a": int, Optional[int]: int}, False),
        ({"a": 1, "b": "x"}, {"a": int, Optional[Any]: int}, False),
        ({"a": 1, "b": "x"}, {"a": int, Optional[str]: Any}, True),
        ({"a": 1, "b": "x"}, {"a": int, Optional[str]: str}, True),
    ),
)
def test_matches(data, schema, expected):  # *note: is unsupported
    assert (
        sut.matches(data, schema) == expected
    ), f"matches : {(data, schema, expected)!r}"


def test_pred_hash():
    a = sut.Union[int, str, Tuple[int]]
    b = sut.Union[str, int, Tuple[int]]
    assert a == b
    assert b == a
    assert hash(a) == hash(b)


def test_union():
    a = sut.Union[int, str]
    b = sut.Union[str, int, float]
    c = a | b
    assert c == sut.Union[int, str, float]
    # pylint: disable-next=protected-access
    assert c._args == (
        int,
        str,
        float,
    ), "preserves order"


def no_args():
    pass


def no_args_any() -> Any:
    return True


def no_args_int() -> int:
    return 1


def int_int(a: int) -> int:
    return a


def int_none(_a: int) -> None:
    return


@pytest.mark.parametrize(
    "fun, schema, expected",
    (
        (None, Callable, False),
        (no_args, Callable[..., int], False),
        (no_args, Callable[..., float], False),
        (no_args, Callable[..., None], True),
        (no_args, Callable[..., Any], True),
        (no_args, Callable[[], int], False),
        (no_args, Callable[[], float], False),
        (no_args, Callable[[], None], True),
        (no_args, Callable[[], Any], True),
        (no_args, Callable[[int], None], False),
        (no_args, Callable[[float], None], False),
        (no_args_any, Callable[..., int], False),
        (no_args_any, Callable[..., float], False),
        (no_args_any, Callable[..., None], False),
        (no_args_any, Callable[..., Any], True),
        (no_args_any, Callable[[], int], False),
        (no_args_any, Callable[[], float], False),
        (no_args_any, Callable[[], None], False),
        (no_args_any, Callable[[], Any], True),
        (no_args_any, Callable[[int], Any], False),
        (no_args_any, Callable[[float], Any], False),
        (no_args_int, Callable[..., int], True),
        (no_args_int, Callable[..., float], False),
        (no_args_int, Callable[..., None], False),
        (no_args_int, Callable[..., Any], True),
        (no_args_int, Callable[[], int], True),
        (no_args_int, Callable[[], float], False),
        (no_args_int, Callable[[], None], False),
        (no_args_int, Callable[[], Any], True),
        (no_args_int, Callable[[int], Any], False),
        (no_args_int, Callable[[float], Any], False),
        (int_int, Callable[..., int], True),
        (int_int, Callable[..., float], False),
        (int_int, Callable[..., None], False),
        (int_int, Callable[..., Any], True),
        (int_int, Callable[[], int], True),
        (int_int, Callable[[], float], False),
        (int_int, Callable[[], None], False),
        (int_int, Callable[[], Any], True),
        (int_int, Callable[[int], Any], True),
        (int_int, Callable[[float], Any], False),
        (int_int, Callable[[int, ...], Any], True),
        (int_int, Callable[[float, ...], Any], False),
        (int_none, Callable[..., int], False),
        (int_none, Callable[..., float], False),
        (int_none, Callable[..., None], True),
        (int_none, Callable[..., Any], True),
        (int_none, Callable[[], int], False),
        (int_none, Callable[[], float], False),
        (int_none, Callable[[], None], True),
        (int_none, Callable[[], Any], True),
        (int_none, Callable[[int], Any], True),
        (int_none, Callable[[float], Any], False),
    ),
)
def test_matches_callable(fun, schema, expected):
    if fun is not None:
        assert sut.matches_callable(fun, Callable) is True
    sut.matches_callable_breakpoint = not (
        sut.matches_callable(fun, schema) == expected
    )
    assert (
        sut.matches_callable(fun, schema) == expected
    ), f"matches : {(fun, schema, expected)!r}"
