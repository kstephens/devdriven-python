from typing import Any
from dataclasses import dataclass


@dataclass
class Maybe:
    "Represents a value which may or may not exist."
    exists: bool
    value: Any

    def __bool__(self) -> bool:
        return bool(self.exists)

    def __call__(self) -> Any:
        return self.value

    def __str__(self) -> str:
        return f"({self.exists}, {self.value!r})"

    def __repr__(self) -> str:
        return f"Maybe({self.exists!r}, {self.value!r})"
