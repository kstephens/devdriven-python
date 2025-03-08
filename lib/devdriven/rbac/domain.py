from dataclasses import dataclass, field
from .identity import (
    User,
    Users,
    Group,
    Groups,
    Identity,
    UserPass,
    UserPasses,
    Tokens,
)
from .rbac import Role, Roles, Membership, Memberships, Rule, Rules, Request
from .util import find


@dataclass
class IdentityDomain:
    users: Users = field(default_factory=list)
    groups: Groups = field(default_factory=list)

    def user_by_name(self, name: str) -> User:
        return find(lambda x: x.name == name, self.users)

    def group_by_name(self, name: str) -> Group:
        return find(lambda x: x.name == name, self.groups)

    def groups_for_user(self, user: User) -> Groups:
        return user.groups


@dataclass
class RoleDomain:
    memberships: Memberships = field(default_factory=list)
    roles: Roles = field(default_factory=list)

    def role_by_name(self, name: str) -> Role:
        return find(lambda x: x.name == name, self.roles)

    def roles_for_user(self, user: User) -> Roles:
        roles = [memb.role for memb in self.memberships_for_identity(user)]
        for group in user.groups:
            roles.extend(self.roles_for_group(group))
        return roles

    def roles_for_group(self, group: Group) -> Roles:
        return [memb.role for memb in self.memberships_for_identity(group)]

    def memberships_for_identity(self, member: Identity) -> Memberships:
        def pred(membership: Membership) -> bool:
            return (
                isinstance(membership.member, type(member))
                and membership.member.name == member.name
            )

        return [membership for membership in self.memberships if pred(membership)]


@dataclass
class RuleDomain:
    rules: Rules = field(default_factory=list)

    def find_rules(
        self, request: Request, roles: Roles, max_rules: int | None = None
    ) -> Rules:
        rules = []
        for rule in self.rules:
            if self.rule_matches(request, roles, rule):
                rules.append(rule)
                if max_rules and len(rules) >= max_rules:
                    break
        return rules

    def rule_matches(self, request: Request, roles: Roles, rule: Rule) -> bool:
        if not rule.action.matches(request.action):
            return False
        if not rule.resource.matches(request.resource):
            return False
        for role in roles:
            if rule.role.matches(role):
                return True
        return False


@dataclass
class PasswordDomain:
    passwords: UserPasses = field(default_factory=list)

    def password_for_user(self, user: User) -> UserPass | None:
        for password in self.passwords:
            if password.username == user.name:
                return password
        return None


@dataclass
class TokenDomain:
    tokens: Tokens = field(default_factory=list)


@dataclass
class AuthDomain:
    identity_domain: IdentityDomain
    password_domain: PasswordDomain
    token_domain: TokenDomain


@dataclass
class Domain:
    identity_domain: IdentityDomain
    role_domain: RoleDomain
    rule_domain: RuleDomain
    password_domain: PasswordDomain

    def find_rules(self, request: Request, max_rules: int | None = None) -> Rules:
        return self.rule_domain.find_rules(
            request, self.role_domain.roles_for_user(request.user), max_rules
        )

    def user_for_name(self, name: str) -> User:
        user = self.identity_domain.user_by_name(name)
        if user and not user.groups:
            user.groups = self.identity_domain.groups_for_user(user)
        return user

    def group_by_name(self, name: str) -> Group:
        return self.identity_domain.group_by_name(name)

    def role_by_name(self, name: str) -> Role:
        return self.role_domain.role_by_name(name)

    def roles_for_user(self, user: User) -> Roles:
        roles = [memb.role for memb in self.memberships_for_identity(user)]
        for group in user.groups:
            roles.extend([memb.role for memb in self.memberships_for_identity(group)])
        return roles

    def memberships_for_identity(self, identity: Identity) -> Memberships:
        return self.role_domain.memberships_for_identity(identity)

    def password_for_user(self, user: User) -> UserPass | None:
        return self.password_domain.password_for_user(user)

    def token_by_name(self, user: User) -> UserPass | None:
        return self.password_domain.password_for_user(user)


@dataclass
class Solver:
    domain: Domain

    def find_rules(self, request: Request, max_rules: int | None = None) -> Rules:
        return self.domain.find_rules(request, max_rules)
