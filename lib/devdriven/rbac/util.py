from typing import Any, Callable, Iterable, List

Composable = Callable[..., Any]
Composable1 = Callable[[Any], Any]


def find(pred: Callable[[Any], bool], seq: Iterable, default: Any = None) -> Any:
    for item in seq:
        if pred(item):
            return item
    return default


def getter(name: str) -> Composable1:
    return lambda obj: getattr(obj, name)


def mapcat(func: Callable[[Any], Iterable], seq: Iterable) -> Iterable:
    result: List = []
    for item in seq:
        result.extend(func(item))
    return result


def cartesian_product(dims: Iterable[Iterable[Any]]) -> Iterable[Iterable[Any]]:
    def collect(dims, rows):
        if not dims:
            return rows
        new = []
        for row in rows:
            for val in dims[0]:
                new.append(append_one(row, val))
        return collect(dims[1:], new)

    dims = tuple(dims)
    return collect(dims[1:], [[val] for val in dims[0]])


def append_one(x: list, y: Any) -> list:
    x = x.copy()
    x.append(y)
    return x


def comp1(f: Composable1, g: Composable1) -> Composable1:
    return lambda x: f(g(x))


def comp(f: Composable1, g: Composable) -> Composable:
    return lambda *args: f(g(*args))
