"""
Basic schema checker.
The themes:
- inspired by the widely used Clojure https://github.com/plumatic/schema.
- homoiconicity: ubiquitous Python data structures are annotated with schema predicates.
- data structure and the schema are walked in parallel.
- non-predicates values are expected to be equal under `==`, i.e atomic values: strings, numbers.
- typing.* predicates are supported, where possible.
-`typing.Union` is a special case and is simulated with `Union[]` below.
"""

import inspect
import re
import types
import typing
from abc import abstractmethod
from functools import reduce
from icecream import ic  # pylint: disable=unused-import


# We need access to the `_*` classes to determine how to process typing instances by metatype:
# pylint: disable=protected-access
# mypy: disable-error-code=attr-defined

NoneType = type(None)


class Halt(BaseException)
    pass


class Walk:
    def root(self, x, s):
        self.halt = None
        self.init_root(x, s)
        try:
            self.walk_root(x, s)
        except Halt as exc:
            self.halt = exc

    def halt(self, reason):
        halt = Halt()
        halt.reason = reason
        raise halt

    def walk(self, x, s):
        getattr(self, f"walk_{type(x)}")(x, s)

    def walk_dict(self, x, s):
        for k, v in x.items():
            self.walk_dict_kv(k, v, k, s.get(v))

    def walk_kv(self, k, v, ks, vs):
        self.walk(k, ks)
        self.walk(v, vs)

    def walk_list(self, x, s):
        self.walk_list_before(x, s)
        self.walk_iterable(x, s, list)
        self.walk_list_after(x, s)

    def walk_tuple(self, x, s):
        self.walk_tuple_before(x, s)
        self.walk_iterable(x, s, tuple)
        self.walk_tuple_after(x, s)

    def walk_set(self, x, s):
        self.walk_set_before(x, s)
        self.walk_iterable(x, s, set)
        self.walk_set_after(x, s)

    def walk_iterable(self, x, s, typ):
        for v in x:
            self.walk_elem(v, s, typ)

    def walk_elem(self, x, s, typ):
        self.walk(x, s)

class Match(Walk):
    def root(self, x, s):
        super().root(x, s)

    def fail(self, k, s):
        self.halt((k, s))

    def walk_dict_kv(k, v, ks, vs):
        self.walk(k, ks)
        self.walk(v, vs)

    def walk_list(self, x, s):
        self.walk_iterable(x, s, list)

    def walk_tuple(self, x, s):
        self.walk_iterable(x, s, tuple)

    def walk_set(self, x, s):
        self.walk_iterable(x, s, set)

    def walk_iterable(self, x, s, typ):
        if not isinstance(type(x), type):
            self.halt(x, s)
        for v in x:
            self.walk_item(v, s)

    def walk_other(self, x, s):
        self.matches_other(x, s)

    def matches_other(self, x, s):
        if isinstance(s, type) and not isinstance(x, s):
            self.halt(x, s)


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


# pylint: disable-next=too-many-locals
def matches_dict(x, s) -> bool:
    """
    Match each (sk, sv) with each (k,v).
    All unmatched (k, v) must match at least one optional (sk, sv).
    """
    if not isinstance(x, dict):
        return False
    len_x, len_s = len(x), len(s)
    len_x_matched = len_s_matched = 0
    x_unmatched = x.copy()
    optionals = []
    for skv in s.items():
        sk, sv = skv
        is_opt, opt_sk = optional_key(sk)
        if is_opt:
            optionals.append((opt_sk, sv))
            continue
        skv_matched = 0
        for k, v in list(x_unmatched.items()):
            if matches(k, sk) and matches(v, sv):
                len_x_matched += (skv_matched := 1)
                x_unmatched.pop(k)
        if skv_matched:
            len_s_matched += 1
    if optionals:
        for k, v in x_unmatched.items():
            for sk, sv in optionals:
                if matches(k, sk) and matches(v, sv):
                    len_x_matched += 1
                    break
        return len_x_matched >= len_x
    return len_x_matched == len_x and len_s_matched == len_s


def optional_key(k):
    if k in (Ellipsis, typing.Optional, object):
        return True, typing.Any
    if isinstance(k, typing._UnionGenericAlias):
        return True, k
    return False, None


def matches_atom(x, s) -> bool:
    if s in (Ellipsis, typing.Any, typing.Optional):
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
    if s == typing.Callable:
        return callable(x)
    if isinstance(s, typing._CallableGenericAlias):
        return matches_callable(x, s)
    if callable(s):
        return s(x)
    return False


def matches_type(x, s) -> bool:
    # Callable[..., None]:
    if s is NoneType and (x is None or x is inspect._empty):
        return True
    if s in (Ellipsis, typing.Any):
        return True
    if (x is s) or (x == s):
        return True
    if isinstance(s, typing._UnionGenericAlias):
        return any(matches_type(x, t) for t in s.__args__)
    if isinstance(x, type) and isinstance(s, type) and issubclass(x, s):
        return True
    # This is likely to be incomplete.
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


def matches_callable(x, s):
    if not callable(x):
        return False
    # pylint: disable-next=unidiomatic-typecheck
    if type(s) is typing._CallableType:
        return True
    sig = inspect.signature(x)
    *s_parameters, s_return_annotation = s.__args__
    if not matches_type(sig.return_annotation, s_return_annotation):
        return False
    if s_parameters is Ellipsis:
        return True
    sig_params = tuple(sig.parameters.values())
    for i, ps in enumerate(s_parameters):
        if ps == Ellipsis:
            return True
        if i >= len(sig_params):
            return False
        if not matches_type(sig_params[i].annotation, ps):
            return False
    return True


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

    @abstractmethod
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
        "Flatten nested Unions."
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
        """
        Union type order is irrelevant.
        The natural choice here is: set(self._args) == set(other._args)
        BUT some types are NOT hashable.
        """
        return (
            self is other
            or type(self) is type(other)
            and is_same_set(self._args, other._args)
        )

    def __hash__(self):
        "__hash__ cannot be inherited"
        return super().__hash__()


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
    "Make Pred repr look like typing.* objects."
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


def nav(x, *path):
    "Navigate a data structure by keys or callable."
    for p in path:
        try:
            if callable(p):
                x = p(x)
            else:
                x = x[p]
        except Exception as e:  # pylint: disable=broad-exception-caught
            return e
    return x
