from typing import Any, Self, Callable, Iterable
from dataclasses import dataclass, field
import re
from .identity import User  # , Group

Matcher = Callable[[Any, Any], bool]

def match_name(self, other):
  return self.name == other.name
def match_false(_self, _other):
  return False
def match_true(_self, _other):
  return True
def regex_matcher(regex) -> Matcher:
  return lambda _self, other: re.search(regex, other.name) is not None
def negate_matcher(matcher: Matcher) -> Matcher:
  def negated(a: Any, b: Any) -> bool:
    return not matcher(a, b)
  return negated

class Matchable:
  def __init__(self, name: str, description: str = '', matcher: Matcher = match_name):
    self.name = name
    self.description = description
    self.matcher = matcher
    self.regex = None

  def matches(self, other: Self) -> bool:
    return self.matcher(self, other)

  def __str__(self):
    return f"{self.__class__.__name__}({self.name!r}, {self.description!r}, {self.regex!r})"

  def __repr__(self):
    return self.__str__()

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
  description: str = field(default='')

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
  roles: Roles = field(default_factory=list)  # ???
