import json
import subprocess
import re
import dataclasses
import inspect
from dataclasses import dataclass
from typing import Any, Optional
from datetime import datetime
from pathlib import Path
from devdriven.util import maybe_decode_bytes, datetime_iso8601

class ToDict:
  def __init__(self):
    self.handlers = DEFAULT_HANDLERS

  def __call__(self, data: Any) -> Any:
    return self.walk(data)

  def walk(self, obj: Any) -> Any:
    if obj is None:
      return None
    if callable(getattr(obj, 'to_dict', None)):  # https://stackoverflow.com/a/54625079
      try:
        return self.walk(obj.to_dict())
      except Exception as exc:
        # print(repr(type(obj)))
        # print(repr(obj))
        return f'<< {repr(obj)} >>'
        # raise exc
    obj_type = type(obj)
    if issubclass(obj_type, int) or issubclass(obj_type, float) or issubclass(obj_type, str):
      return obj
    if issubclass(obj_type, bytes):
      decoded = maybe_decode_bytes(obj)
      if decoded:
        return f'<BYTES[{len(obj)}]:{decoded}>'
      return f'<BYTES[{len(obj)}]>'
    if issubclass(obj_type, dict):
      walked = {}
      for key, val in obj.items():
        walked[self.walk(key)] = self.walk(val)
      return walked
    if dataclasses.is_dataclass(obj_type):
      rep = {
        'class': obj_type,
        'fields': dataclasses.asdict(obj),
      }
      return self.walk(rep)
    if inspect.isclass(obj):
      return repr(obj)
    if issubclass(obj_type, list) or issubclass(obj_type, tuple):
      return [self.walk(elem) for elem in obj]
    if issubclass(obj_type, re.Pattern):
      return repr(obj)
    if issubclass(obj_type, Path):
      return repr(obj)
    if issubclass(obj_type, datetime):
      return datetime_iso8601(obj)
    if issubclass(obj_type, subprocess.CompletedProcess):
      return self.walk(vars(obj))
    if issubclass(obj_type, BaseException):
      return self.walk_exception(obj)
    return {'class': obj_type.__name__, 'repr': repr(obj)}

  def walk_exception(self, obj: Any) -> Any:
    obj_type = type(obj)
    if issubclass(obj_type, subprocess.CalledProcessError):
      return self.walk({
        'class': obj_type.__name__,
        'message': str(obj),
        'returncode': obj.returncode,
        'stdout': obj.stdout,
        'stderr': obj.stderr
      } | vars(obj))
    if issubclass(obj_type, OSError):
      return self.walk({
        'class': obj_type.__name__,
        'message': str(obj),
        'errno': obj.errno,
        'strerror': obj.strerror,
        'filename': obj.filename,
        'filename2': obj.filename2
      } | vars(obj))
    return self.walk({
      'class': obj_type.__name__,
      'message': str(obj)
    } | vars(obj))

  def match(self, obj):
    obj_type = type(obj)
    for handler in self.handlers:
      result = handler.match(self, obj, obj_type)
      if result is not UNMATCHED:
        return result
    return self.default_result(obj, obj_type)

  def default_result(self, obj, obj_type):
    return {'class': obj_type.__name__, 'repr': repr(obj)}

def to_dict(data: Any) -> Any:
  return ToDict().walk(data)

def dump_json(obj: Any, indent: Optional[int] = None) -> str:
  return json.dumps(to_dict(obj), indent=indent)

UNMATCHED = object()

#####################################

@dataclass
class Handler():
  name: str = ''
  matcher: callable = None
  def match(self, walk, obj, obj_type):
    return self.matcher(walk, obj, obj_type)

  def parse_lines(self, lines):
    def eat_empty():
      while lines and not lines[0]:
        lines.pop(0)
    eat_empty()
    if not lines:
      return None
    name = lines.pop(0)
    body = [lines.pop(0)]
    while lines and lines[0].startswith('  '):
      body.append(lines.pop(0))
    body.append('  return UNMATCHED')
    return Handler(name, self.make_fun(['walk', 'obj', 'obj_type'], body))

  def make_fun(self, params, body):
    SEQUENCE[0] += 1
    seq = SEQUENCE[0]
    name = f'handler_fun_{seq}'
    expr = f'def {name}({", ".join(params)}):\n  ' + '\n  '.join(body) + '\n'
    print(expr)
    bindings = globals() | {'UNMATCHED': UNMATCHED}
    exec(expr, bindings)
    return bindings[name]

SEQUENCE = [0]

def parse_handlers(defs):
  handlers = []
  lines = defs.splitlines()
  while handler := lines and Handler().parse_lines(lines):
    handlers.append(handler)
  return handlers

DEFAULT_HANDLERS = parse_handlers(
'''

'''
)

#import pprint
#pprint.pprint(DEFAULT_HANDLERS)