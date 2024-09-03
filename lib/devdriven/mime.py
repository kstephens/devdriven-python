from typing import Optional, List, Tuple
import mimetypes
import re
from pathlib import Path

MimeType = Tuple[Optional[str], Optional[str]]

LONG_SUFFIX_RX = re.compile(r'(?:^|/)[^.]+(\.[^/]+)$')
def short_and_long_suffix(path: str) -> Tuple[str, str]:
  short_suffix = long_suffix = Path(path).suffix
  if m := re.search(LONG_SUFFIX_RX, str(path)):
    long_suffix = m[1]
  return short_suffix, long_suffix

def content_type_for_suffixes(suffixes: List[str], default=(None, None)) -> MimeType:
  for suffix in suffixes:
    content_type, content_encoding = guess_type('a' + suffix)
    if content_type:
      return content_type, content_encoding
  return default

def guess_type(file: str) -> MimeType:
  content_type, content_encoding = mimetypes.guess_type(file)
  if not content_type:
    content_type, content_encoding = MIMETYPES_MORE.get(Path(file).suffix, MIMETYPES_MORE[None])
  return content_type, content_encoding


MIMETYPES_MORE = {
  '.md': ('text/markdown', None),
  '.markdown': ('text/markdown', None),
  None: (None, None),
}
