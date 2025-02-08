from typing import Optional, List, Tuple, Dict
import mimetypes
import re
import platform
from pathlib import Path

MimeType = Tuple[Optional[str], Optional[str]]

LONG_SUFFIX_RX = re.compile(r"(?:^|/)[^.]+(\.[^/]+)$")


def short_and_long_suffix(path: str) -> Tuple[str, str]:
    short_suffix = long_suffix = Path(path).suffix
    if m := LONG_SUFFIX_RX.search(str(path)):
        long_suffix = m[1]
    return short_suffix, long_suffix


def content_type_for_suffixes(suffixes: List[str], default=(None, None)) -> MimeType:
    for suffix in suffixes:
        content_type, content_encoding = guess_type("a" + suffix)
        if content_type:
            return content_type, content_encoding
    return default


def guess_type(file: str) -> MimeType:
    suffix = Path(file).suffix
    if override := MIMETYPES_OVERRIDE.get(suffix):
        return override
    content_type, content_encoding = mimetypes.guess_type(file)
    if not content_type:
        content_type, content_encoding = MIMETYPES_MORE.get(
            suffix, MIMETYPES_MORE[None]
        )
    return content_type, content_encoding


MimeTypeDict = Dict[str | None, MimeType]
MIMETYPES_OVERRIDE: MimeTypeDict = {}
MIMETYPES_MORE: MimeTypeDict = {
    None: (None, None),
}

# Behave like Linux:
if platform.system() == "Darwin":
    MIMETYPES_OVERRIDE.update(
        {
            ".c": ("text/x-csrc", None),
            ".h": ("text/x-chdr", None),
            ".cc": ("text/x-c++src", None),
            ".cpp": ("text/x-c++src", None),
            ".cxx": ("text/x-c++src", None),
            ".hh": ("text/x-c++hdr", None),
            ".hpp": ("text/x-c++hdr", None),
            ".hxx": ("text/x-c++hdr", None),
            ".o": ("application/x-object", None),
        }
    )
    MIMETYPES_MORE.update(
        {
            ".md": ("text/markdown", None),
            ".markdown": ("text/markdown", None),
        }
    )
