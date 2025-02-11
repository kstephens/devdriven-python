from typing import Any
from uuid import UUID, uuid4
from random import Random, SystemRandom

DEFAULT = SystemRandom()
CURRENT = None
SEED = None


def random() -> Random:
    return CURRENT or DEFAULT


def set_seed(seed: Any) -> Random:
    # pylint: disable-next=global-statement
    global CURRENT, SEED
    SEED = str(seed)
    CURRENT = Random()
    CURRENT.seed(SEED, version=2)
    return CURRENT


def get_seed() -> str | None:
    return SEED


def uuid() -> str:
    if CURRENT:
        return str(UUID(bytes=random().randbytes(16), version=4))
    return str(uuid4())
