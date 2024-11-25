from dataclasses import dataclass, field, fields
from icecream import ic


def object_methods(obj):
    cls = type(obj)
    return [
        method_name for method_name in dir(cls) if callable(getattr(obj, method_name))
    ]


def object_properties(obj):
    cls = type(obj)
    return [p for p in dir(cls) if isinstance(getattr(cls, p), property)]


def object_fields(obj):
    cls = type(obj)
    return fields(cls)


@dataclass
class A:
    a: int
    b: str


a = A(1, "a")
ic(a)
ic(object_methods(a))
ic(object_properties(a))
ic(object_fields(a))
ic(a.a)
ic(a.b)


@dataclass
class AMock(A):
    @property
    def a(self):
        return 2

    @a.setter
    def set_a(self, _x):
        pass


m = AMock(1, "a")
ic(m)
ic(object_methods(m))
ic(object_properties(m))
ic(object_fields(m))
ic(m.a)
ic(m.b)
