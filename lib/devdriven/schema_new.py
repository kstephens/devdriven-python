"""
Basic schema checker.
Does not implement all of typing, but close enough for most things.
"""

import re
import types
import typing
from contextlib import contextmanager


# We need access to the `_*` classes to determine how to process typing instances by metatype.
# pylint: disable=protected-access
# mypy: disable-error-code=attr-defined


class Match:
    def __init__(self):
        self.path = []
        self._path_stack = []
        self.context = None
        self._context_stack = []
        self.error = None
        self.errors = []

    @property
    def ok(self):
        return self.error is None

    def __bool__(self):
        return self.ok

    def scan(self, x, schema):
        self.matches(x, schema)
        return self

    @contextmanager
    def path_context(self, *path):
        self._path_stack.append(self.path)
        self.path = self.path.copy()
        self.path.append(path)
        try:
            yield
        finally:
            self.path = self._path_stack.pop()

    def matches(self, x, schema):
        self._context_stack.append(self.context)
        self.context = (x, schema)
        try:
            path = self.path
            result = self.matches_internal(x, schema)
            if not result and self.error is None:
                self.error = (path, self.context)
                self.errors.append(self.error)
            return result
        finally:
            self.context = self._context_stack.pop()

    def matches_internal(self, x, schema) -> bool:
        if isinstance(schema, dict):
            return self.matches_dict(x, schema)
        if isinstance(schema, (list, tuple)):
            return self.matches_seq(x, schema)
        return self.matches_atom(x, schema)

    def matches_seq(self, x, schema) -> bool:
        if type(x) is not type(schema):
            with self.path_context("type!=", type(x), type(schema)):
                return False
        x = tuple(x)
        if len(x) != len(schema):
            with self.path_context("length!=", len(x), len(schema)):
                return False
        for i, (v, s) in enumerate(zip(x, schema)):
            with self.path_context("[]", i):
                if not self.matches(v, s):
                    return False
        return True

    def matches_dict(self, x, schema) -> bool:
        "Note: x may contain additional k that are not specified in schema"
        if not isinstance(x, dict):
            return False

        def match_kv(k, v):
            # If schema[k] exists, presume sk is not a pattern,
            # and match v against sv:
            with self.path_context("{}", k):
                if k in schema:
                    return self.matches(v, schema[k])
                # Otherwise, scan for a (sk,kv) that matches (k,v):
                for sk, sv in schema.items():
                    if self.matches_internal(k, sk) and self.matches_internal(v, sv):
                        return True
                # No (k,v) matches (sk,sv):
                return False

        # For each (k,v) at least one (sk,kv) must match:
        for k, v in x.items():
            if not match_kv(k, v):
                return False
        # Every schema pattern was matched:
        return True

    def matches_atom(self, x, s) -> bool:
        if s is typing.Any:
            return True
        if (x is s) or (x == s):
            return True
        with self.path_context(str(repr(s))):
            if isinstance(s, Pred):
                return s.matches(self, x)
            if isinstance(s, re.Pattern) and isinstance(x, str):
                return re.search(s, x) is not None
            if s is typing.Tuple:
                return isinstance(x, s.__origin__)
            if isinstance(s, typing._UnionGenericAlias):
                return any(self.matches_internal(x, t) for t in s.__args__)
            if isinstance(s, typing._LiteralGenericAlias):
                return x in s.__args__
            if isinstance(s, (type, types.UnionType)):
                return isinstance(x, s)
            if isinstance(s, typing._SpecialGenericAlias):
                return isinstance(x, s.__origin__)
            if isinstance(s, typing._GenericAlias):
                return self.matches_typing_generic_alias(x, s)
            if isinstance(s, typing._Final):
                raise ValueError("cannot match on {s!r}")
            if callable(s):
                return s(x)
            return False

    def matches_typing_generic_alias(self, x, s) -> bool:
        with self.path_context(repr(s)):
            if s.__origin__ is tuple:
                if not isinstance(x, s.__origin__):
                    return False
                if len(x) != len(s.__args__):
                    with self.path_context("length!=", len(x), len(s.__args__)):
                        return False
                for i, (e, t) in enumerate(zip(x, s.__args__)):
                    with self.path_context("[]", i):
                        if not self.matches(e, t):
                            return False
                return True
            if s.__origin__ in (list, set):
                if not isinstance(x, s.__origin__):
                    return False
                return all(self.matches_internal(v, s.__args__[0]) for v in x)
            if s.__origin__ is dict:
                if not isinstance(x, s.__origin__):
                    return False
                sk, sv = s.__args__
                return all(
                    self.matches_internal(k, sk) and self.matches_internal(v, sv)
                    for k, v in x.items()
                )
        return False


def scan(x, schema) -> Match:
    return Match().scan(x, schema)


def matches(x, schema) -> bool:
    return scan(x, schema).ok


def check(x, schema):
    match = Match().scan(x, schema)
    if not match.ok:
        raise SchemaError(repr(match.error))
    return x


class SchemaError(Exception):
    pass


class Pred:
    def __init__(self, *args):
        self._args = args

    def matches(self, _m, _x) -> bool:
        return False  # pragma: no cover

    def __or__(self, other):
        return Union(self, other)

    def __repr__(self):
        return f"{type(self).__name__}({",".join(map(repr, self._args))})"


class Is(Pred):
    def matches(self, _m, x) -> bool:
        return x is self._args[0]


class Equal(Pred):
    def matches(self, _m, x) -> bool:
        return x == self._args[0]


class Type(Pred):
    def matches(self, _m, x) -> bool:
        # pylint: disable-next=unidiomatic-typecheck
        return type(x) is self._args[0]


class Union(Pred):
    def matches(self, m, x) -> bool:
        return any(m.matches_internal(x, s) for s in self._args)


def dict_shape(x):
    if isinstance(x, dict):
        return {k: dict_shape(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        x = [dict_shape(v) for v in x]
        return [v for v in x if v is not None]
    return None
