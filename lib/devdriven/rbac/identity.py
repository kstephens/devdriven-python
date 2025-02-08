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


@dataclass
class Password:
    name: str
    password: str = field(default="")


@dataclass
class Token:
    name: str
    token: str = field(default="")


Identity = User | Group
Users = Iterable[User]
Passwords = Iterable[Password]
Tokens = Iterable[Token]
