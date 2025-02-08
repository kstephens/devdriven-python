from typing import Optional, Any, List
import platform
import os
import pickle
import bz2
from .util import exec_command


def read_file(name: str, encoding: Optional[str] = None) -> Optional[bytes | str]:
    try:
        if encoding:
            with open(name, "r", encoding=encoding) as input_io:
                return input_io.read()
        else:
            with open(name, "rb") as input_io:
                return input_io.read()
    except OSError:
        return None


def read_file_lines(name: str, encoding: str = "utf-8") -> Optional[List[str]]:
    try:
        return str(read_file(name, encoding=encoding)).splitlines()
    except (OSError, UnicodeDecodeError):
        return None


def delete_file(path: str) -> bool:
    try:
        os.remove(path)
        return True
    except OSError:
        return False


def file_md5(file: str, md5_cmd: Optional[str] = None) -> Optional[str]:
    if not md5_cmd:
        md5_cmd = "md5" if platform.system() == "Darwin" else "md5sum"
    result = exec_command(
        [md5_cmd, file], check=False, capture_output=True, encoding="utf-8"
    )
    if result.returncode == 0:
        if md5_cmd.endswith("md5sum"):
            return str(result.stdout.split(" ")[0]).strip()
        return str(result.stdout.split(" = ")[1]).strip()
    return None


def file_size(path: str) -> Optional[int]:
    try:
        return os.stat(path).st_size
    except FileNotFoundError:  # might be a symlink to bad file.
        return None


BUFFER_SIZE = 8192
NEWLINE_BYTE = b"\n"[0]


def file_nlines(
    path: str, eol: bytes = b"\n", buffer_size: int = BUFFER_SIZE
) -> Optional[int]:
    # For large files: wc -l 'path' will be faster.
    last_buffer = None
    count = byte_count = 0
    assert len(eol) == 1
    try:
        with open(path, "rb") as input_io:
            while buf := input_io.read(buffer_size):
                last_buffer = buf
                count += buf.count(eol)
                byte_count += len(buf)
        if byte_count == 0:
            return 0
        if last_buffer and last_buffer[-1] == NEWLINE_BYTE:
            return count
        return count + 1
    except OSError:
        return None


def pickle_bz2(file: str, mode: str, data: Any = None) -> Any:
    if mode == "rb":
        with bz2.open(file, "rb") as stream:
            return pickle.load(stream)
    with bz2.open(file, "wb") as stream:
        pickle.dump(data, stream)
        return data
