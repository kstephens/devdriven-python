"""
Basic schema checker.
Does not implement all of typing, but close enough for most things.
"""

import re
import types
import typing
from functools import reduce
from icecream import ic  # pylint: disable=unused-import


# We need access to the `_*` classes to determine how to process typing instances by metatype.
# pylint: disable=protected-access
# mypy: disable-error-code=attr-defined


def matches(x, schema):
    if isinstance(schema, dict):
        return matches_dict(x, schema)
    if isinstance(schema, (list, tuple)):
        return matches_seq(x, schema)
    return matches_atom(x, schema)


def matches_seq(x, schema) -> bool:
    if type(x) is not type(schema):
        return False
    # [1, 2, 3] matches [1, 2, ...]
    if len(schema) > 0 and schema[-1] == Ellipsis:
        x = x[: len(schema) - 1]
        schema = schema[:-1]
    if len(x) != len(schema):
        return False
    return all(matches(v, s) for v, s in zip(x, schema))


def matches_dict(x, schema) -> bool:
    "Note: x may contain additional k that are not specified in schema"
    if not isinstance(x, dict):
        return False

    def match_kv(k, v):
        # If schema[k] exists, presume sk is not a pattern,
        # and match v against sv:
        if k in schema:
            return matches(v, schema[k])
        # Otherwise, scan for any (sk,kv) that matches (k,v):
        return any(matches(k, sk) and matches(v, sv) for sk, sv in schema.items())

    # For each (k,v) at least one (sk,kv) must match:
    return all(match_kv(k, v) for k, v in x.items())


def matches_atom(x, s) -> bool:
    if s is typing.Any:
        return True
    if (x is s) or (x == s):
        return True
    if isinstance(s, Pred):
        return s.matches(x)
    if isinstance(s, re.Pattern) and isinstance(x, str):
        return re.search(s, x) is not None
    if s is typing.Tuple:
        return isinstance(x, s.__origin__)
    if isinstance(s, typing._UnionGenericAlias):
        return any(matches(x, t) for t in s.__args__)
    if isinstance(s, typing._LiteralGenericAlias):
        return x in s.__args__
    if isinstance(s, (type, types.UnionType)):
        return isinstance(x, s)
    if isinstance(s, typing._SpecialGenericAlias):
        return isinstance(x, s.__origin__)
    if isinstance(s, typing._GenericAlias):
        return matches_typing_generic_alias(x, s)
    if isinstance(s, typing._Final):
        raise ValueError("cannot match on {s!r}")
    if callable(s):
        return s(x)
    return False


def matches_typing_generic_alias(x, s) -> bool:
    if not isinstance(x, s.__origin__):
        return False
    # Tuple[a, b, c]:
    if s.__origin__ is tuple:
        return matches_seq(x, s.__args__)
    # List[a], Set[t]:
    if s.__origin__ in (list, set):
        assert len(s.__args__) == 1
        return all(matches(v, s.__args__[0]) for v in x)
    # Dict[k, v]:
    if s.__origin__ is dict:
        assert len(s.__args__) == 2
        sk, sv = s.__args__
        return all(matches(k, sk) and matches(v, sv) for k, v in x.items())
    return False


class Meta(type):
    # Pred[...] => Pred(...):
    def __getitem__(cls, arg):
        # Pred[x, y, ...] -> Pred((x, y, ...)):
        if isinstance(arg, tuple):
            return cls(arg)._simplify()
        # Pred[x] -> Pred((x)):
        return cls((arg,))._simplify()


class Pred(metaclass=Meta):
    def __init__(self, args):
        self._args = args
        self._hash = 0

    def matches(self, _x) -> bool:
        return False  # pragma: no cover

    def _simplify(self):
        return self

    # Pred | Any => Union[a, b]
    def __or__(self, other):
        return Union((self, other))._simplify()

    # Any | Pred => Union[a, b]
    def __ror__(self, other):
        return Union((self, other))._simplify()

    def __repr__(self):
        return f"{type(self).__module__}.{type(self).__name__}[{", ".join(map(schema_repr, self._args))}]"

    def __eq__(self, other):
        return self is other or type(self) is type(other) and self._args == other._args

    def __hash__(self):
        return self._hash_()

    def _hash_(self):
        self._hash = self._hash or reduce(compose_hash, self._args, hash(type(self)))
        return self._hash


class Is(Pred):
    "Is the same object."
    def matches(self, x) -> bool:
        return x is self._args[0]


class Equal(Pred):
    "Is equal."
    def matches(self, x) -> bool:
        return x == self._args[0]


class TypeIs(Pred):
    "Has exact type."
    def matches(self, x) -> bool:
        # pylint: disable-next=unidiomatic-typecheck
        return type(x) is self._args[0]


class Union(Pred):
    def matches(self, x) -> bool:
        return any(matches(x, s) for s in self._args)

    def _simplify(self):
        assert isinstance(self._args, tuple)
        args, flat = list(self._args), []
        while args:
            s = args.pop(0)
            if isinstance(s, Union):
                args.extend(s._args)
            elif s not in flat:
                flat.append(s)
        self._args = tuple(flat)
        return self

    def __eq__(self, other):
        return (
            self is other
            or type(self) is type(other)
            and is_same_set(self._args, other._args)
        )

    def __hash__(self):
        return self._hash_()


def compose_hash(h, x):
    "Compose hash values."
    try:
        return h ^ hash(x)
    except TypeError:
        return h


def is_same_set(a, b):
    "Compare sets with unhashable elements."
    if len(a) != len(b):
        return False
    return all(x in a for x in b)


def schema_repr(s):
    if isinstance(s, type):
        return s.__qualname__
    if isinstance(s, list):
        return schema_repr_items("[", s, "]")
    if isinstance(s, tuple):
        return schema_repr_items("(", s, ")")
    if isinstance(s, set):
        return schema_repr_items("{", s, "}")
    if isinstance(s, dict):
        return (
            "{"
            + ",".join(f"{schema_repr(k)}: {schema_repr(v)}" for k, v in s.items())
            + "}"
        )
    if s == Ellipsis:
        return "..."
    return repr(s)


def schema_repr_items(b, s, e):
    return b + ",".join(schema_repr(v) for v in s) + e


def dict_shape(x):
    if isinstance(x, dict):
        return {k: dict_shape(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)):
        x = [dict_shape(v) for v in x]
        return type(x)(v for v in x if v is not None)
    return None
