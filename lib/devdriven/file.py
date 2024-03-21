from typing import Optional, Union, List, Tuple
import os
import pickle
import bz2
from .util import exec_command

def read_file(name: str, encoding: Optional[str] = None) -> Optional[Union[bytes, str]]:
  try:
    if encoding:
      with open(name, 'r', encoding=encoding) as input_io:
        return input_io.read()
    else:
      with open(name, 'rb') as input_io:
        return input_io.read()
  except OSError:
    return None

def read_file_lines(name: str, encoding: str = 'utf-8') -> Optional[List[str]]:
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

def file_md5(file: str) -> Optional[str]:
  result = exec_command(['md5sum', file], check=False, capture_output=True)
  if result.returncode == 0:
    return str(result.stdout.decode('utf-8').split(' ')[0])
  return None

def file_size(path: str) -> Optional[int]:
  try:
    return os.stat(path).st_size
  except FileNotFoundError:  # might be a symlink to bad file.
    return None

def file_nlines(path: str) -> Optional[int]:
  try:
    count, byte_count, last_buffer = file_count_substr(path, b'\n')
    if byte_count == 0:
      return 0
    if last_buffer and last_buffer[-1] == NEWLINE_BYTE:
      return count
    return count + 1
  except OSError:
    return None

def file_count_substr(path: str, substr: bytes) -> Tuple[int, int, Optional[bytes]]:
  last_buffer = None
  count = byte_count = 0
  with open(path, 'rb') as input_io:
    while buf := input_io.read(BUFFER_SIZE):
      last_buffer = buf
      count += buf.count(substr)
      byte_count += len(buf)
  return (count, byte_count, last_buffer)


BUFFER_SIZE = 8192
NEWLINE_BYTE = b'\n'[0]

def read_write_pickle(file, mode, data=None):
  with bz2.open(file, mode) as stream:
    if mode == 'rb':
      return pickle.load(stream)
    pickle.dump(data, stream)
    return data
