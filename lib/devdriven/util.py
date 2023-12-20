import os
import subprocess
import logging
import inspect
import time
import re
import sys
import dataclasses
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Any, Iterable, List, Dict, Callable, Tuple, Union, Optional
from collections import defaultdict

Predicate = Callable[[Any], Any]
Func1 = Callable[[Any], Any]
FuncAny = Callable[..., Any]
SubprocessResult = Any  # subprocess.CompletedProcess

def get_safe(items, key, default=None):
  try:
    return items[key]
  except (KeyError, IndexError):
    return default

def shorten_string(a_str, max_len, placeholder='...'):
  if len(a_str) > max_len:
    end = max(0, max_len - len(placeholder) + 1)
    return a_str[:end] + placeholder
  return a_str

def maybe_decode_bytes(obj: Optional[bytes], encoding: str = 'utf-8') -> Optional[str]:
  try:
    return obj and obj.decode(encoding)
  except UnicodeDecodeError:
    return None


# See: https://en.wikipedia.org/wiki/ISO_8601
DATETIME_ISO8601_FMT = '%Y-%m-%d %H:%M:%S.%f%z'
# DATETIME_ISO8601_FMT = '%Y%m%dT%H%M%S.%f%z'
# pylint: disable-next=invalid-name
def datetime_iso8601(dt: Any, tz=None) -> Union[str, Any]:
  if not tz:
    tz = timezone.utc
  return (dt and dt.replace(tzinfo=tz).strftime(DATETIME_ISO8601_FMT))

def convert_windows_timestamp_to_iso8601(ts_str):
  # pylint: disable-next=invalid-name
  ts = int(ts_str) / 1000
  # pylint: disable-next=invalid-name
  dt = datetime.fromtimestamp(ts)
  return datetime_iso8601(dt)

def reorder_list(items, front, back):
  front = [i for i in front if i in items]
  back = [i for i in back if i in items]
  middle = items
  middle = [i for i in middle if i not in front]
  middle = [i for i in middle if i not in back]
  return front + middle + back

def parse_commands(argv: List[str]) -> List[List[str]]:
  cmds = []
  argvi = iter(argv)
  command = None
  while arg := next(argvi, None):
    if arg == ',':
      if command is not None:
        cmds.append(command)
      command = None
    else:
      if command is None:
        command = []
      command.append(arg)
  if command:
    cmds.append(command)
  return cmds

def exec_command(cmd_line: List[str], **options: Any) -> SubprocessResult:
  msg = f'exec_command : {repr(cmd_line)} : ...'
  logging.info('%s', msg)
  (result, dt_ms) = elapsed_ms(subprocess.run, cmd_line, **options)
  logging.info(
    '%s',
    ''.join([
      msg,
      f' : returncode {result.returncode} : ',
      f'stdout {len_or_none(result.stdout)} bytes : ',
      f'stderr {len_or_none(result.stderr)} bytes : ',
      f'elapsed_ms {dt_ms:.3f}'])
  )
  result.elapsed_ms = dt_ms
  return result

def exec_command_unless_dry_run(cmd_line: List[str], dry_run: bool, **options: Any) -> Optional[SubprocessResult]:
  if dry_run:
    logging.info('DRY-RUN : exec_command : %s', repr(cmd_line))
    return None
  return exec_command(cmd_line, **options)

def file_md5(file: str) -> Optional[str]:
  result = exec_command(['md5sum', file], check=False, capture_output=True)
  if result.returncode == 0:
    return str(result.stdout.decode('utf-8').split(' ')[0])
  return None

def len_or_none(obj: Any) -> Optional[int]:
  return len(obj) if obj else None

def none_as_blank(value: Any) -> Any:
  return '' if value is None else value

def read_file(name: str, default: Any = None) -> Union[bytes, Any]:
  try:
    with open(name, 'rb') as input_io:
      return input_io.read()
  except OSError:
    return default

def read_file_lines(name: str, default: Any = None) -> Union[List[str], Any]:
  try:
    return read_file(name).decode('utf-8').splitlines()
  # pylint: disable=broad-except
  except Exception:
    return default

def delete_file(path: str) -> bool:
  try:
    os.remove(path)
    return True
  except OSError:
    return False

def elapsed_ms(func: FuncAny, *args: Any, **kwargs: Any) -> Tuple[Any, float]:
  time_0 = time.time()
  result = func(*args, **kwargs)
  time_1 = time.time()
  return (result, (time_1 - time_0) * 1000)

def file_size(path: str, default: Any = None) -> Any:
  try:
    return os.stat(path).st_size
  except FileNotFoundError:  # might be a symlink to bad file.
    return default

def file_nlines(path: str, default: Any = None) -> Union[int, Any]:
  last_byte = None
  count = byte_count = 0
  try:
    with open(path, 'rb') as input_io:
      while buf := input_io.read(8192):
        last_byte = buf[-1]
        count += buf.count(b'\n')
        byte_count += len(buf)
  except OSError:
    return default
  if byte_count == 0:
    return 0
  if last_byte == b'\n'[0]:
    return count
  return count + 1

def first(iterable: Iterable[Any], condition: Predicate = lambda x: True, default: Any = None) -> Any:
  for elem in iterable:
    if condition(elem):
      return elem
  return default

def flat_map(iterable: Iterable[Any], func: FuncAny, *args: Any, **kwargs: Any) -> Iterable[Any]:
  return [elem for sublist in iterable for elem in func(sublist, *args, **kwargs)]

def split_flat(items, sep):
  return flat_map(items, lambda x: x.split(sep))

def parse_range(x, n):
  if m := re.match(r'^(-?\d+)?:(-?\d+)?(?::(-?\d+))?$', x):
    if m[0] == '-' or m[1] == '-' or m[2] == '-':
      return None
    return make_range(int(m[1] or 0), int(m[2] or n), int(m[3] or 1), n)
  return None

def make_range(start, end, step, n):
  if not start:
    start = 0
  if not end:
    end = n
  if not step:
    step = 1
  if step == 0:
    return None
  if start < 0:
    start = n + start
  if end < 0:
    end = n + end
  if step > 0 and start > end:
    step = - step
  return range(start, end, step)

def partition(seq: Iterable[Any], pred: Predicate) -> Tuple[List[Any], List[Any]]:
  true_elems: List[Any] = []
  false_elems: List[Any] = []
  for elem in seq:
    (true_elems if pred(elem) else false_elems).append(elem)
  return (true_elems, false_elems)

def frequency(seq: Iterable[Any]) -> Dict[Any, int]:
  counts: Dict[Any, int] = defaultdict(lambda: 0, {})
  for elem in seq:
    counts[elem] += 1
  return dict(counts.items())

def chunks(items, width):
  width = max(1, width)
  return (items[i: i + width] for i in range(0, len(items), width))

def uniq_by(seq: Iterable[Any], key: Func1) -> Iterable[Any]:
  seen = set()
  result = []
  for elem in seq:
    val = key(elem)
    if val not in seen:
      seen.add(val)
      result.append(elem)
  return result

def not_implemented() -> None:
  raise NotImplementedError(inspect.stack()[1][3])

@contextmanager
def cwd(path: str) -> Any:
  oldpwd = os.getcwd()
  os.chdir(path)
  try:
    yield
  finally:
    os.chdir(oldpwd)

def printe(x):
  print(x, file=sys.stderr)

def glob_to_rx(glob, glob_terminator=None):
  assert not glob_terminator
  rx = glob
  rx = rx.replace('.', r'[^/]')
  rx = rx.replace('*', r'[^/]*')
  rx = rx.replace('?', r'[^/][^/]?')
  return re.compile(r'^' + rx + r'$')

def set_from_match(obj, match: re.Match):
  setattr_from_dict(obj, match.groupdict())

def setattr_from_dict(obj, attrs):
  for name, val in attrs.items():
    setattr(obj, name, val)

def dataclass_from_dict(klass, opts, defaults=None):
  defaults = defaults or {}
  args = {f.name: opts.get(f.name, defaults.get(f.name, None))
          for f in dataclasses.fields(klass) if f.init}
  return klass(**args)

def unpad_lines(lines):
  lines = lines.copy()
  while lines and not lines[0]:
    lines.pop(0)
  for line in lines:
    if m := re.match(r'^( +)', line):
      pad = re.compile(f'^{m[1]}')
      break
  return [re.sub(pad, '', line) for line in lines]

def wrap_words(words, width, _punctuation=r'[.,?;:]'):
  result = []
  current = ''
  rx = re.compile(r'^(?P<left>.*?)(?P<sep>\s+|\n|[.,?;:])(?P<rest>.*)')
  while words:
    if m := re.match(rx, words):
      words = m['rest']
      current += m['left'] + m['sep']
    else:
      break
    if not 0 < len(current) <= width:
      result.append(current)
      current = ''
  if current:
    current += words
    result.append(current)
  return result

def module_fullname(obj):
  '''
  Does not work as expected.
  '''
  klass = obj.__class__
  module = klass.__module__
  if module == 'builtins':
    return klass.__qualname__  # avoid outputs like 'builtins.str'
  return module + '.' + klass.__qualname__
