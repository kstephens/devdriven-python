from typing import Any, Optional, Self, Callable, List, Type, IO
from dataclasses import dataclass, field
import re
import devdriven.glob

Matcher = Callable[[Any, Any], bool]

class Matchable:
  def __init__(self, name: str):
    self.name = name
    self.matcher: Matcher = match_name

  def matches(self, other: Self) -> bool:
    return self.matcher(self, other)

def match_name(self: Matchable, other: Matchable):
  return self.name == other.name
def match_false(_self, _other):
  return False
def match_true(_self, _other):
  return True

class Resource(Matchable):
  def nothing(self):
    return None

class Action(Matchable):
  def nothing(self):
    return None

class Role(Matchable):
  def nothing(self):
    return None


Resources = List[Resource]
Roles = List[Role]

@dataclass
class Permission:
  name: str

@dataclass
class Rule:
  resource: Resource
  action: Action
  role: Role
  permission: Permission


Permissions = List[Permission]
Rules = List[Rule]

########################################

@dataclass
class RoleMembership:
  role: Role
  member: Any


RoleMemberships = List[RoleMembership]

@dataclass
class Group:
  name: str


Groups = List[Group]

@dataclass
class Identity:
  name: str
  groups: Groups = field(default_factory=list)


Identities = List[Identity]

########################################

@dataclass
class Domain:
  roles: Roles
  role_memberships: RoleMemberships
  rules: Rules

@dataclass
class Request:
  resource: Resource
  action: Action
  identity: Identity
  roles: Roles = field(default_factory=list)

########################################

@dataclass
class IdentityRoles:
  domain: Domain

  def identity_roles(self, identity: Identity) -> Roles:
    roles = []
    for role_memb in self.domain.role_memberships:
      # ic(role_memb)
      for group in identity.groups:
        # ic(group)
        if role_memb.member.name == group.name:
          roles.append(role_memb.role)
    return roles

@dataclass
class Solver:
  domain: Domain

  def find_rules(self, request: Request) -> Rules:
    rules = []
    request.roles = IdentityRoles(self.domain).identity_roles(request.identity)
    # ic(request)
    for rule in self.domain.rules:
      # ic(rule)
      if self.rule_matches(rule, request):
        rules.append(rule)
    return rules

  def rule_matches(self, rule: Rule, request: Request) -> bool:
    if not rule.action.matches(request.action):
      return False
    if not rule.resource.matches(request.resource):
      return False
    for role in request.roles:
      if rule.role.matches(role):
        return True
    return False

@dataclass
class TextLoader:
  resource: Resource

  def read(self, io: IO) -> Rules:
    rules = []
    while line := io.readline():
      if rule := self.parse_line(line):
        rules.append(rule)
    return rules

  def parse_line(self, line: str) -> Optional[Rule]:
    trimmed = re.sub(COMMENT_RX, '', line)
    trimmed = trimmed.strip()
    if trimmed == '':
      return None
    if m := re.search(RULE_RX, trimmed):
      return Rule(
        resource=self.parse_pattern(Resource, f"{self.resource.name}/{m['resource']}", False),
        action=self.parse_pattern(Action, m['action'], True),
        role=self.parse_pattern(Role, m['role'], True),
        permission=Permission(m['permission']),
      )
    raise Exception(f"invalid line: {line!r}")

  def parse_pattern(self, constructor: Type, pattern: str, star_always_matches: bool) -> Any:
    obj = constructor(name=pattern)
    if star_always_matches and pattern == '*':
      obj.matcher = match_true
    else:
      def matcher(self, other):
        # ic((self.regex, other.name))
        return re.search(self.regex, other.name) is not None
      obj.regex = devdriven.glob.glob_to_regex(pattern)
      obj.matcher = matcher
    return obj


COMMENT_RX = re.compile(r'#.*$')
LEADING_SPACE_RX = re.compile(r'^\s+')
RULE_RX = re.compile(r'^(?P<permission>\S+)\s+(?P<action>\S+)\s+(?P<role>\S+)\s+(?P<resource>\S+)$')
