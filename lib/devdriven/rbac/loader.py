from typing import Any, Optional, Callable, Iterable, List, Type, IO
from dataclasses import dataclass, field
from pathlib import Path
import re
import logging
from .identity import User, Users, Group, Groups
from .rbac import Resource, Action, Rule, Rules, Permission, \
  Role, Roles, Membership, Memberships, \
  match_true, regex_matcher, negate_matcher
from .domain import Domain, IdentityDomain, RoleDomain, RuleDomain
from .util import getter, mapcat
from ..path import clean_path
from ..glob import glob_to_regex

@dataclass
class TextLoader:
  prefix: str = field(default='')

  def read_rules(self, io: IO) -> Rules:
    return parse_lines(io, RULE_RX, self.parse_rule_line)

  def parse_rule_line(self, m: re.Match) -> Rules:
    result: List[Rule] = []
    permission = Permission(m['permission'])
    for action in parse_list(m['action']):
      for role in parse_list(m['role']):
        for resource in parse_list(m['resource']):
          resource_path = clean_path(f"{self.prefix}{resource}")
          rule = Rule(
            permission=permission,
            action=self.parse_pattern(Action, action, True),
            role=self.parse_pattern(Role, role, True),
            resource=self.parse_pattern(Resource, resource_path, False),
          )
          logging.debug(
            '  rule: %s',
            f"{rule.permission.name} {rule.action.name}"
            f"{rule.role.name} {rule.resource.name}"
            f" # {(rule.resource.regex and rule.resource.regex.pattern)!r}"
          )
          result.append(rule)
    return result

  def parse_pattern(self, constructor: Type, pattern: str, star_always_matches: bool) -> Any:
    if negate := pattern.startswith('!'):
      pattern = pattern.removeprefix('!')
    if pattern == '*' and star_always_matches:
      regex = None
      matcher = match_true
      description = pattern
    else:
      regex = glob_to_regex(pattern)
      # pylint: disable-next=unnecessary-lambda-assignment
      matcher = regex_matcher(regex)
      description = repr(regex)
    if negate:
      matcher = negate_matcher(matcher)
      description = f"!{description}"
    obj = constructor(name=pattern, description=pattern, matcher=matcher)
    obj.regex = regex
    return obj

  ##############################

  def read_users(self, io: IO) -> Users:
    return parse_lines(io, USER_RX, self.parse_user_line)

  def parse_user_line(self, m: re.Match) -> Users:
    groups = [Group(group, group) for group in parse_list(m['groups'])]

    def make_user(name):
      return User(name, f"@{name}", groups=groups.copy())
    return [make_user(name) for name in parse_list(m['user'])]

  ##############################

  def read_memberships(self, io: IO) -> Memberships:
    return parse_lines(io, MEMBERSHIP_RX, self.parse_membership_line)

  def parse_membership_line(self, m: re.Match) -> Memberships:
    role = Role(m['role'])
    return [self.make_membership(role, member) for member in m['members'].split(',')]

  def make_membership(self, role: Role, description: str) -> Membership:
    if description.startswith('@'):
      name = description.removeprefix('@')
      return Membership(role=role, member=User(name, description))
    return Membership(role=role, member=Group(description, description))


COMMENT_RX = re.compile(r'#.*$')
LEADING_SPACE_RX = re.compile(r'^\s+')
RULE_RX = re.compile(r'rule\s+(?P<permission>\S+)\s+(?P<action>\S+)\s+(?P<role>\S+)\s+(?P<resource>\S+)')
MEMBERSHIP_RX = re.compile(r'member\s+(?P<role>\S+)\s+(?P<members>\S+)')
USER_RX = re.compile(r'user\s+(?P<user>\S+)\s+(?P<groups>\S+)')


def real_open_file(file: Path) -> Optional[IO]:
  try:
    return open(str(file), "r", encoding='utf-8')
  except OSError:
    return None

@dataclass
class DomainFileLoader:
  users_file: Path
  memberships_file: Path
  resource_root: Path
  resource: Path
  users: Users = field(default_factory=list)
  groups: Groups = field(default_factory=list)
  memberships: Memberships = field(default_factory=list)
  roles: Roles = field(default_factory=list)
  files_loaded: List[Path] = field(default_factory=list)

  def load_domain(self) -> Domain:
    with open(self.users_file, encoding='utf-8') as io:
      self.users = TextLoader().read_users(io)
      self.files_loaded.append(Path(self.users_file))
    with open(self.memberships_file, encoding='utf-8') as io:
      self.memberships = TextLoader().read_memberships(io)
      self.files_loaded.append(Path(self.memberships_file))
    groups = {}
    for user in self.users:
      for group in user.groups:
        groups[group.name] = group
    self.groups = sorted(groups.values(), key=getter('name'))
    roles = {}
    for member in self.memberships:
      roles[member.role.name] = member.role
    self.roles = sorted(roles.values(), key=getter('name'))
    loader = FileSystemLoader(resource_root=self.resource_root)
    rules_for_resource = loader.load_rules(self.resource)
    self.files_loaded.extend(loader.files_loaded)

    return Domain(
      identity_domain=IdentityDomain(users=self.users, groups=self.groups),
      role_domain=RoleDomain(memberships=self.memberships, roles=self.roles),
      rule_domain=RuleDomain(rules=rules_for_resource),
    )

  def show(self, prt=print):
    prt("")
    for user in self.users:
      prt(f"#  user {user.name} {','.join(map(getter('name'), user.groups))}")
    for membership in self.memberships:
      prt(f"#  member {membership.role.name} {membership.member.name}")
    for role in self.roles:
      prt(f"#  role {role.name}")

@dataclass
class FileSystemLoader:
  resource_root: Path
  open_file: Callable = field(default=real_open_file)
  auth_file_name: str = field(default='.rbac.txt')
  files_loaded: List[Path] = field(default_factory=list)

  def load_rules(self, resource: Path) -> Rules:
    return mapcat(self.load_auth_file, self.resource_paths(resource))

  def load_auth_file(self, path: Path) -> Rules:
    auth_file = self.auth_file(path)
    io: IO = self.open_file(auth_file)
    if io:
      loader = TextLoader(prefix=str(path) + '/')
      self.files_loaded.append(auth_file)
      return loader.read_rules(io)
    return []

  def resource_paths(self, resource: Path) -> Iterable[Path]:
    return list(resource.parents)

  def auth_file(self, path: Path) -> Path:
    return self.resource_root / path.relative_to('/') / self.auth_file_name

###################################

def parse_lines(io: IO, rx: re.Pattern, parser: Callable) -> Iterable[Any]:
  result: List[Any] = []
  while line := io.readline():
    if m := re.match(rx, trim_line(line)):
      result.extend(parser(m))
  return result

def parse_list(val: str) -> Iterable[str]:
  return re.split(r'\s*,\s', val)

def trim_line(line: str) -> str:
  line = line.removesuffix('\n')
  line = re.sub(r'^\s+|\s+$', '', line)
  return re.sub(COMMENT_RX, '', line)
