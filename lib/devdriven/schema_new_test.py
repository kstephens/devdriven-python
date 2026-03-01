import re
from typing import Any, Dict, List, Literal, Set, Tuple, Union
import pytest
from icecream import ic  # pylint: disable=unused-import
from . import schema_new as sut


obj = object()

MyDict = Dict[str, int]


@pytest.mark.parametrize(
    "data, schema, expected",
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
        (obj, sut.Is(obj), True),
        (3, sut.Is(obj), False),
        (2, sut.Equal(2), True),
        (2.0, sut.Equal(2), True),
        (3.0, sut.Equal(2), False),
        (2, Literal[2, 3], True),
        (3, Literal[2, 3], True),
        (5, Literal[2, 3], False),
        (None, MyDict, False),
        ({"a": 1}, MyDict, True),
        ({"a": "b"}, MyDict, False),
        (None, Tuple[int, float], False),
        ((2, 3.5), Tuple[int, float], True),
        ((2, "x"), Tuple[int, float], False),
        ((2,), Tuple[int, float], False),
        (None, Set[int], False),
        ({2, 3}, Set[int], True),
        ({2, "x"}, Set[int], False),
        (999, Union[int, Union[float, list]], True),
    ),
)
def test_matches(data, schema, expected):
    assert (
        sut.matches(data, schema) == expected
    ), f"matches({data!r}, {schema!r}) == {expected!r}"

    assert bool(sut.scan(data, schema)) is expected

    if expected is False:
        assert sut.scan(data, schema).error is not None
        with pytest.raises(sut.SchemaError):
            sut.check(data, schema)
    else:
        assert sut.scan(data, schema).error is None
        assert sut.check(data, schema) is data
