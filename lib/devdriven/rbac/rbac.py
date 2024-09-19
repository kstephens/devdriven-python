from typing import Any, Optional, Self, Callable, List, Dict, Type, IO
from dataclasses import dataclass, field
from pathlib import Path
import re
import devdriven.glob
# from icecream import ic

Matcher = Callable[[Any, Any], bool]

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
  description: str = field(default='')

  def brief(self) -> str:
    return f"({self.resource.name!r}, {self.action.name!r}, {self.role.name!r}, {self.permission.name!r})"


Permissions = List[Permission]
Rules = List[Rule]

########################################

@dataclass
class Membership:
  role: Role
  member: Any


Memberships = List[Membership]

@dataclass
class Group:
  name: str
  description: str = field(default='')


Groups = List[Group]

@dataclass
class User:
  name: str
  description: str = field(default='')
  groups: Groups = field(default_factory=list)


Users = List[User]

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
class UserRoles:
  domain: Domain

  def user_roles(self, user: User) -> Roles:
    roles = []
    for role_memb in self.domain.memberships:
      for group in user.groups:
        if role_memb.member.name == group.name:
          roles.append(role_memb.role)
    return roles

@dataclass
class Solver:
  domain: Domain

  def find_rules(self, request: Request) -> Rules:
    rules = []
    request.roles = UserRoles(self.domain).user_roles(request.user)
    for rule in self.domain.rules:
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
  prefix: str

  def read_rules(self, io: IO) -> Rules:
    rules = []
    while line := io.readline():
      if rule := self.parse_rule(line):
        rules.append(rule)
    return rules

  def parse_rule(self, line: str) -> Optional[Rule]:
    if not (trimmed := trim_line(line)):
      return None
    if m := re.search(RULE_RX, trimmed):
      resource_path = clean_path(f"{self.prefix}{m['resource']}")
      return Rule(
        resource=self.parse_pattern(Resource, f"{resource_path}", False),
        action=self.parse_pattern(Action, m['action'], True),
        role=self.parse_pattern(Role, m['role'], True),
        permission=Permission(m['permission']),
      )
    return None

  def parse_pattern(self, constructor: Type, pattern: str, star_always_matches: bool) -> Any:
    obj = constructor(name=pattern)
    if star_always_matches and pattern == '*':
      obj.matcher = match_true
    else:
      def matcher(self, other):
        return re.search(self.regex, other.name) is not None
      obj.regex = devdriven.glob.glob_to_regex(pattern)
      obj.description = obj.regex
      obj.matcher = matcher
    return obj

  ##############################

  def read_users(self, io: IO) -> Users:
    result: Users = []
    while line := io.readline():
      if user := self.parse_user(line):
        result.append(user)
    return result

  def parse_user(self, line: str) -> Optional[User]:
    if not (trimmed := trim_line(line)):
      return None
    if m := re.search(USER_RX, trimmed):
      name = m['user']
      user = User(name, f"@{name}")
      user.groups = [Group(group, group) for group in m['groups'].split(',')]
      return user
    return None

  ##############################

  def read_memberships(self, io: IO) -> Memberships:
    result: Memberships = []
    while line := io.readline():
      if memberships := self.parse_memberships(line):
        result.extend(memberships)
    roles: Dict[str, Role] = {}
    members: Dict[str, Any] = {}
    for memb in result:
      roles[memb.role.name] = memb.role = roles.get(memb.role.name, memb.role)
      members[memb.member.name] = memb.member = roles.get(memb.member.name, memb.member)
    return result

  def parse_memberships(self, line: str) -> Optional[Memberships]:
    if not (trimmed := trim_line(line)):
      return None
    if m := re.search(MEMBERSHIP_RX, trimmed):
      role = Role(m['role'])
      return [make_membership(role, member) for member in m['members'].split(',')]
    return None

def read_lines(io: IO, proc: Callable) -> Any:
  while line := io.readline():
    if trimmed := trim_line(line):
      proc(trimmed)

def make_membership(role, name: str):
  if name.startswith('@'):
    return Membership(
      role=role,
      member=User(name.removeprefix('@'), name),
    )
  return Membership(
    role=role,
    member=Group(name, name),
  )

def trim_line(line: str) -> str:
  line = line.removesuffix('\n')
  line = re.sub(r'^\s+|\s+$', '', line)
  return re.sub(COMMENT_RX, '', line)

def real_open_file(file: Path) -> Optional[IO]:
  try:
    return open(str(file), "r", encoding='utf-8')
  except OSError:
    return None

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


COMMENT_RX = re.compile(r'#.*$')
LEADING_SPACE_RX = re.compile(r'^\s+')
RULE_RX = re.compile(r'^\s*perm\s+(?P<permission>\S+)\s+(?P<action>\S+)\s+(?P<role>\S+)\s+(?P<resource>\S+)\s*$')
MEMBERSHIP_RX = re.compile(r'^\s*member\s+(?P<role>\S+)\s+(?P<members>\S+)\s*$')
USER_RX = re.compile(r'^\s*user\s+(?P<user>\S+)\s+(?P<groups>\S+)\s*$')

@dataclass
class FileSystemLoader:
  root: Path
  open_file: Callable = field(default=real_open_file)

  def load_rules(self, resource: Path) -> Rules:
    resource_paths = self.resource_paths(resource)
    rules = []
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

  def resource_paths(self, resource: Path) -> List[Path]:
    return list(resource.parents)

  def auth_file(self, path: Path) -> Path:
    return self.root / path.relative_to('/') / '.auth.txt'
