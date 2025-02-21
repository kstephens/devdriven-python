from typing import Any, Callable
import logging
from pathlib import Path
from .file import pickle_bz2


class PickleCache:
    def __init__(self, path: str, generate: Callable | None):
        self.path = Path(path)
        self.generate = generate
        self._data: Any = None
        self._ready: bool = False
        self._stale: bool = False

    @property
    def ready(self) -> bool:
        return self._ready

    def exists(self) -> bool:
        return self.path.exists()

    def is_ready(self) -> bool:
        return self._ready

    def flush(self) -> None:
        self.path.unlink(True)
        self._stale = True

    @property
    def data(self) -> Any:
        return self.get_data()

    @data.setter
    def data(self, data: Any) -> None:
        self.set_data(data)
        self.write(self.path)

    def get_data(self) -> Any:
        logging.debug("%s", f"get_data : {self.path!r}")
        if not self._ready:
            if self.exists():
                self.read(self.path)
            else:
                assert self.generate
                self.set_data(self.generate())
                self.write(self.path)
        assert self._ready
        return self._data

    def set_data(self, data: Any) -> None:
        logging.debug("%s", f"set_data : {self.path!r}")
        self._data = data
        self._ready = True
        self._stale = True

    def write(self, path: Path) -> None:
        logging.debug("%s", f"write : {path!r}")
        assert self._ready
        pickle_bz2(str(path), "wb", self._data)
        self._stale = False

    def read(self, path: Path) -> None:
        logging.debug("%s", f"read : {path!r}")
        self._data = pickle_bz2(str(path), "rb")
        self._ready = True
