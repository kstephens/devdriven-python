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


Users = Iterable[User]
Identity = User | Group
