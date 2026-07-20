import pytest
from icecream import ic  # pylint: disable=unused-import

import ntpg.schema as schema
import ntpg.schema as sut

NoneType = type(None)


def first_where(f, seq, default=None):
    for x in seq:
        if f(x):
            return x
    return default


def partition(pred, seq):
    "a contains all x in where pred(x)."
    a, b = [], []
    for x in seq:
        (a if pred(x) else b).append(x)
    return a, b


def dict_essential_shape(x):
    """
    Trims down a deep dictionary structure into it essential shape.
    Useful for human inspection of deep structures.
    """
    if isinstance(x, dict):
        return {k: dict_essential_shape(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)):
        return type(x)(filter(lambda v: v is not None, map(dict_essential_shape, x)))
    return type(x)


def dict_essential_types(x):
    """
    Recursively replace leaf values with their type.
    Useful for human inspection of deep structures.
    """
    if isinstance(x, dict):
        return {k: dict_essential_shape(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)):
        return type(x)(filter(lambda v: v is not None, map(dict_essential_shape, x)))
    return type(x)


def transpose(x):
    """
    Traverses a data structure and generates all path to atoms, of the form:
    ((t0, k0), ..., (t, v))
    Where
    - v is an atom and t = type(v).
    - t0 is the type of the container: dict, list, tuple, set.
    - k0 is the "key" to the next position.
    """
    stack = [([], x)]
    while stack:
        path, x = stack.pop()
        t = type(x)
        if isinstance(x, dict):
            for k, v in x.items():
                stack.append((path + [(t, k)], v))
        elif isinstance(x, (list, tuple)):
            for i, e in enumerate(x):
                stack.append((path + [(t, i)], e))
        elif isinstance(x, set):
            for e in x:
                stack.append((path + [(t, None)], e))
        else:
            yield path + [(t, x)]


@pytest.mark.parametrize(
    "data, expected",
    (
        (None, None),
        (2, None),
        ([2, None, 3], []),
        ({2, None}, {}),
        ((2, None), ()),
        (
            {
                "a": 2,
                "b": None,
                "c": [2, None, 3],
            },
            {"a": None, "b": None, "c": []},
        ),
    ),
)
def xtest_dict_essential_shape(data, expected):
    assert sut.dict_essential_shape(data) == expected


@pytest.mark.parametrize(
    "data, expected",
    (
        (None, NoneType),
        (2, int),
        ([2, None, 3], [int, 3]),
        ({2, None}, {2}),
        ((2, None), (2,)),
        ({"a": 2, "b": None, "c": [2, None, 3]}, {"a": None, "b": None, "c": []}),
    ),
)
def xtest_dict_essential_types(data, expected):
    assert sut.dict_essential_types(data) == expected


@pytest.mark.parametrize(
    "data, expected",
    (
        (None, [[(NoneType, None)]]),
        (5, [[(int, 5)]]),
        (int, [[(type, int)]]),
        (["a", 2], [[(list, 0), (str, "a")], [(list, 1), (int, 2)]]),
        (("a", 2), [[(tuple, 0), (str, "a")], [(tuple, 1), (int, 2)]]),
        ({"a", 2}, [[(set, None), (str, "a")], [(set, None), (int, 2)]]),
        ({"a": 2}, [[(dict, "a"), (int, 2)]]),
        (
            {"a": 2, "b": [1, 2]},
            [
                [(dict, "a"), (int, 2)],
                [(dict, "b"), (list, 0), (int, 1)],
                [(dict, "b"), (list, 1), (int, 2)],
            ],
        ),
    ),
)
def x_test_transpose(data, expected):
    result = list(sut.transpose(data))
    assert len(result) == len(expected)
    assert all(e in result for e in expected)


@pytest.mark.parametrize(
    "data, expected",
    (
        (None, [[(NoneType, None)]]),
        (5, [[(int, 5)]]),
        (int, [[(type, int)]]),
        (["a", 2], [[(list, 0), (str, "a")], [(list, 1), (int, 2)]]),
        (("a", 2), [[(tuple, 0), (str, "a")], [(tuple, 1), (int, 2)]]),
        ({"a", 2}, [[(set, None), (str, "a")], [(set, None), (int, 2)]]),
        ({"a": 2}, [[(dict, "a"), (int, 2)]]),
        (
            {"a": 2, "b": [1, 2]},
            [
                [(dict, "a"), (int, 2)],
                [(dict, "b"), (list, 0), (int, 1)],
                [(dict, "b"), (list, 1), (int, 2)],
            ],
        ),
    ),
)
def test_transpose(data, expected):
    result = list(sut.transpose(data))
    expected = list(expected)
    assert sut.is_same_set(result, expected)


###############################


def matches(x, s):
    return x == s  # placeholder


def keys(x):
    return sorted(x.keys())


def vals(x):
    return [x[k] for k in keys(x)]


def nav(*p):
    result = {}  # placeholder
    expected = {}  # placeholder
    print(repr(p))
    xp = schema.nav(result, *p)
    sp = schema.nav(expected, *p)
    return xp, sp, matches(xp, sp)


def nav_example():
    nav(keys)
    nav("result", "etl", "email", keys)
    nav("result", "etl", "email", "result", keys)
    breakpoint()
    nav("result", "etl", "email", "result", "load", "result", keys)
    path = ("result", "etl", "email", "result", "load", "result", "graph_stats")
    ks = nav(*path, keys)[0]
    ic({k: nav(*path, k) for k in ks})
    ic([k for k in ks if not nav(*path, k)[2]])
