from typing import IO, Callable
from tempfile import NamedTemporaryFile

BUF_SIZE = 8192 * 2

def tempfile_to_writeable(writeable: IO, suffix: str, fun: Callable):
  with NamedTemporaryFile(suffix=suffix) as tmp:
    try:
      fun(tmp.name)
      with open(tmp.name, "rb") as tmp_io:
        while buf := tmp_io.read(BUF_SIZE):
          writeable.write(buf)
    finally:
      tmp.close()

def tempfile_from_readable(readable: IO, suffix: str, fun: Callable):
  with NamedTemporaryFile(suffix=suffix) as tmp:
    try:
      with open(tmp.name, "wb") as tmp_io:
        while buf := readable.read(BUF_SIZE):
          tmp_io.write(buf)
      return fun(tmp.name)
    finally:
      tmp.close()
