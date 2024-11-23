from typing import Any, Optional
import json
import subprocess
import re
import dataclasses
import inspect
from datetime import datetime, timezone
from pathlib import Path
from devdriven.util import maybe_decode_bytes, datetime_iso8601

class ToDict:
  tz = timezone.utc

  def __call__(self, data: Any) -> Any:
    return self.walk(data)

  def walk(self, obj: Any) -> Any:
    if obj is None:
      return None
    if callable(getattr(obj, 'to_dict', None)):  # https://stackoverflow.com/a/54625079
      try:
        return self.walk(obj.to_dict())
      # pylint: disable-next=broad-except
      except Exception as _exc:
        # print(repr(type(obj)))
        # print(repr(obj))
        return f'<< {repr(obj)} >>'
        # raise _exc
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
    if is_dataclass_instance(obj):
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
      return datetime_iso8601(obj.astimezone(self.tz))
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
      })
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

def to_dict(data: Any) -> Any:
  return ToDict().walk(data)

def dump_json(obj: Any, indent: Optional[int] = None) -> str:
  return json.dumps(to_dict(obj), indent=indent)

def is_dataclass_instance(obj: Any) -> bool:
  return dataclasses.is_dataclass(obj) and not isinstance(obj, type)
