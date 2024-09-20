from typing import Any, Optional, Self, Callable, Iterable, List, Dict, Type, IO
from dataclasses import dataclass, field
from pathlib import Path
import re
import devdriven.glob
# from icecream import ic

Matcher = Callable[[Any, Any], bool]
def match_name(self, other):
  return self.name == other.name
def match_false(_self, _other):
  return False
def match_true(_self, _other):
  return True

class Matchable:
  def __init__(self, name: str, desc: str = ''):
    self.name = name
    self.matcher: Matcher = match_name
    self.description = desc

  def matches(self, other: Self) -> bool:
    return self.matcher(self, other)

  def __str__(self):
    return f"{self.__class__.__name__}({self.name!r}, {self.description!r})"

  def __repr__(self):
    return self.__str__()

class Resource(Matchable):
  pass

class Action(Matchable):
  pass

class Role(Matchable):
  pass


Resources = Iterable[Resource]
Roles = Iterable[Role]

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


Permissions = Iterable[Permission]
Rules = Iterable[Rule]

########################################

@dataclass
class Membership:
  role: Role
  member: Any


Memberships = Iterable[Membership]

@dataclass
class Group:
  name: str
  description: str = field(default='')


Groups = Iterable[Group]

@dataclass
class User:
  name: str
  description: str = field(default='')
  groups: Groups = field(default_factory=list)


Users = Iterable[User]

########################################

@dataclass
class Domain:
  roles: Roles
  memberships: Memberships
  rules: Rules

@dataclass
class Request:
  resource: Resource
  action: Action
  user: User
  roles: Roles = field(default_factory=list)

########################################

@dataclass
class Solver:
  domain: Domain

  def find_rules(self, request: Request, max_rules: Optional[int] = None) -> Rules:
    rules = []
    request.roles = self.user_roles(request.user)
    for rule in self.domain.rules:
      if self.rule_matches(rule, request):
        rules.append(rule)
        if max_rules and len(rules) >= max_rules:
          break
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

  def user_roles(self, user: User) -> Roles:
    roles = []
    for role_memb in self.domain.memberships:
      if isinstance(role_memb.member, User) and role_memb.member.name == user.name:
        roles.append(role_memb.role)
      for group in user.groups:
        if isinstance(role_memb.member, Group) and role_memb.member.name == group.name:
          roles.append(role_memb.role)
    return roles

########################################

@dataclass
class TextLoader:
  prefix: str

  def read_rules(self, io: IO) -> Rules:
    return parse_lines(io, RULE_RX, self.parse_rule_line)

  def parse_rule_line(self, m: re.Match) -> Rules:
    result: List[Rule] = []
    permission = Permission(m['permission'])
    for action in split_field(m['action']):
      for role in split_field(m['role']):
        for resource in split_field(m['resource']):
          resource_path = clean_path(f"{self.prefix}{resource}")
          result.append(
            Rule(
              permission=permission,
              action=self.parse_pattern(Action, action, True),
              role=self.parse_pattern(Role, role, True),
              resource=self.parse_pattern(Resource, resource_path, False),
            )
          )
    return result

  def parse_pattern(self, constructor: Type, pattern: str, star_always_matches: bool) -> Any:
    obj = constructor(name=pattern)
    obj.description = pattern
    if negate := pattern.startswith('!'):
      pattern = pattern.removeprefix('!')
    if star_always_matches and pattern == '*':
      matcher = match_true
    else:
      obj.regex = devdriven.glob.glob_to_regex(pattern)
      obj.description = repr(obj.regex)
      # pylint: disable-next=unnecessary-lambda-assignment
      matcher = lambda self, other: re.search(self.regex, other.name) is not None
    if negate:
      negated = matcher
      # pylint: disable-next=unnecessary-lambda-assignment
      matcher = lambda self, other: not negated(self, other)
      obj.description = f"!{obj.description}"
    obj.matcher = matcher
    return obj

  ##############################

  def read_users(self, io: IO) -> Users:
    return parse_lines(io, USER_RX, self.parse_user_line)

  def parse_user_line(self, m: re.Match) -> Users:
    groups = [Group(group, group) for group in split_field(m['groups'])]

    def make_user(name):
      return User(name, f"@{name}", groups=groups.copy())
    return [make_user(name) for name in split_field(m['user'])]

  ##############################

  def read_memberships(self, io: IO) -> Memberships:
    result: Memberships = parse_lines(io, MEMBERSHIP_RX, self.parse_membership_line)
    roles: Dict[str, Role] = {}
    members: Dict[str, Any] = {}
    for memb in result:
      roles[memb.role.name] = memb.role = roles.get(memb.role.name, memb.role)
      members[memb.member.name] = memb.member = roles.get(memb.member.name, memb.member)
    return result

  def parse_membership_line(self, m: re.Match) -> Memberships:
    role = Role(m['role'])
    return [self.make_membership(role, member) for member in m['members'].split(',')]

  def make_membership(self, role: Role, name: str):
    if name.startswith('@'):
      return Membership(
        role=role,
        member=User(name.removeprefix('@'), name),
      )
    return Membership(
      role=role,
      member=Group(name, name),
    )


COMMENT_RX = re.compile(r'#.*$')
LEADING_SPACE_RX = re.compile(r'^\s+')
RULE_RX = re.compile(r'^\s*perm\s+(?P<permission>\S+)\s+(?P<action>\S+)\s+(?P<role>\S+)\s+(?P<resource>\S+)\s*$')
MEMBERSHIP_RX = re.compile(r'^\s*member\s+(?P<role>\S+)\s+(?P<members>\S+)\s*$')
USER_RX = re.compile(r'^\s*user\s+(?P<user>\S+)\s+(?P<groups>\S+)\s*$')


def real_open_file(file: Path) -> Optional[IO]:
  try:
    return open(str(file), "r", encoding='utf-8')
  except OSError:
    return None

@dataclass
class FileSystemLoader:
  root: Path
  open_file: Callable = field(default=real_open_file)

  def load_rules(self, resource: Path) -> Rules:
    resource_paths = self.resource_paths(resource)
    rules: List[Rule] = []
    for path in resource_paths:
      path_rules = self.load_auth_file(path)
      rules.extend(path_rules)
    return rules

  def load_auth_file(self, path: Path) -> Rules:
    auth_file = self.auth_file(path)
    io = self.open_file(auth_file)
    if io:
      loader = TextLoader(prefix=str(path) + '/')
      return loader.read_rules(io)
    return []

  def resource_paths(self, resource: Path) -> Iterable[Path]:
    return list(resource.parents)

  def auth_file(self, path: Path) -> Path:
    return self.root / path.relative_to('/') / '.auth.txt'

###################################

def parse_lines(io: IO, rx: re.Pattern, parser: Callable) -> Iterable:
  result: List = []
  while line := io.readline():
    if m := re.search(rx, trim_line(line)):
      result.extend(parser(m))
  return result

def split_field(val: str) -> Iterable:
  return re.split(r'\s*,\s', val)

def trim_line(line: str) -> str:
  line = line.removesuffix('\n')
  line = re.sub(r'^\s+|\s+$', '', line)
  return re.sub(COMMENT_RX, '', line)

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

def append_one(x, y):
  x = x.copy()
  x.append(y)
  return x

def clean_path(path: str) -> str:
  prev = None
  while path != prev:
    prev = path
    path = re.sub(r'//+', '/', path)
    path = re.sub(r'^\./', '', path)
    path = re.sub(r'^\.\.(?:$|/)', '', path, 1)
    path = re.sub(r'(:?^/)\./', '/', path)
    path = re.sub(r'^/\.\.(?:$|/)', '/', path, 1)
    path = re.sub(r'^[^/]+/\.\.(?:$|/)', '', path, 1)
    path = re.sub(r'/[^/]+/\.\./', '/', path, 1)
  return path
