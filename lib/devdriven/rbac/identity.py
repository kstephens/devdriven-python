from typing import Iterable
from dataclasses import dataclass, field


@dataclass
class Group:
    name: str
    description: str = field(default="")


Groups = Iterable[Group]


@dataclass
class User:
    name: str
    description: str = field(default="")
    groups: Groups = field(default_factory=list)


Username = str
Password = str


@dataclass
class UserPass:
    username: Username
    password: Password


@dataclass
class Token:
    value: str


CookieName = str
CookieValue = str


@dataclass
class Cookie:
    name: CookieName
    value: CookieValue


Identity = User | Group
Users = Iterable[User]
UserPasses = Iterable[UserPass]
Tokens = Iterable[Token]
