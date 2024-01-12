from typing import Optional, List, Tuple
import mimetypes
import re
from pathlib import Path

StrOrNone = Optional[str]

SUFFIX_RX = re.compile(r'(?:^|/)[^.]+(\.[^/]+)$')
def short_and_long_suffix(path: str) -> Tuple[str, str]:
  short_suffix = long_suffix = Path(path).suffix
  if m := re.match(SUFFIX_RX, str(path)):
    long_suffix = m[1]
  return short_suffix, long_suffix

def content_type_for_suffixes(suffixes: List[str], default=(None, None)) -> Tuple[StrOrNone, StrOrNone]:
  for suffix in suffixes:
    content_type, content_encoding = mimetypes.guess_type('anything' + suffix)
    if content_type:
      return content_type, content_encoding
  return default
