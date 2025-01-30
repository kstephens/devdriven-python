from typing import Any, Self, Callable, Iterable
from dataclasses import dataclass, field
import re
from .identity import User  # , Group


class Matchable:
    def __init__(self, name: str, description: str = "", matcher=None):
        self.name = name
        self.description = description
        self.matcher: Matcher = matcher or match_name
        self.regex = None

    def matches(self, other: Self) -> bool:
        return self.matcher(self, other)

    def __str__(self) -> str:
        vals = (self.name, self.description, self.regex)
        return f"{self.__class__.__name__}({', '.join([repr(val) for val in vals if val])})"

    def __repr__(self) -> str:
        return self.__str__()


Matcher = Callable[[Matchable, Matchable], bool]


def match_false(_self: Matchable, _other: Matchable) -> bool:
    return False


def match_true(_self: Matchable, _other: Matchable) -> bool:
    return True


def match_name(self: Matchable, other: Matchable) -> bool:
    return self.name == other.name


def regex_matcher(rx: re.Pattern) -> Matcher:
    return lambda _self, other: rx.search(other.name) is not None


def negate_matcher(matcher: Matcher) -> Matcher:
    def negated(a: Any, b: Any) -> bool:
        return not matcher(a, b)

    return negated


########################################


class Resource(Matchable):
    pass


class Action(Matchable):
    pass


class Role(Matchable):
    pass


@dataclass
class Permission:
    name: str


@dataclass
class Rule:
    permission: Permission
    action: Action
    role: Role
    resource: Resource
    description: str = field(default="")

    def brief(self) -> str:
        return f"({self.permission.name!r}, {self.action.name!r}, {self.role.name!r}, {self.resource.name!r})"


@dataclass
class Membership:
    role: Role
    member: Any


Resources = Iterable[Resource]
Roles = Iterable[Role]
Permissions = Iterable[Permission]
Rules = Iterable[Rule]
Memberships = Iterable[Membership]


@dataclass
class Request:
    resource: Resource
    action: Action
    user: User
