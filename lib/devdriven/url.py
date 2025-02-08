import re
from typing import Any, Optional, Tuple, Literal
from urllib.parse import urlparse, urlunparse, urljoin, ParseResult

FalseVal = Literal[False]
URL = ParseResult
StrOrUrl = str | URL
UrlScheme = str | FalseVal


def url_normalize(url: StrOrUrl, base_url: Optional[StrOrUrl] = None) -> URL:
    if base_url:
        return url_join(base_url, url)
    return url_parse(url)


def url_parse(url: StrOrUrl) -> URL:
    if isinstance(url, str):
        url = urlparse(url)
    return url


def url_is_http(url: URL) -> UrlScheme:
    return url.scheme in ("http", "https") and "http"


def url_is_file(url: URL) -> UrlScheme:
    if url.netloc or url.query or url.fragment:
        return False
    if url.scheme in ("", "file") and not url.netloc:
        return "file"
    return False


def url_is_stdio(url: URL) -> UrlScheme:
    return not url_is_http(url) and url.path == "-" and "-"


def url_scheme(url: URL) -> UrlScheme:
    return url_is_http(url) or url_is_file(url)


def url_join(base: StrOrUrl, url: StrOrUrl) -> URL:
    return urlparse(urljoin(url_to_str(base), url_to_str(url)))


def url_to_str(url: StrOrUrl) -> str:
    if isinstance(url, str):
        return url
    return urlunparse(url)


def url_and_method(
    maybe_method_and_url: str, context: Any = None
) -> Tuple[str, Optional[str]]:
    if context:
        maybe_method_and_url = maybe_method_and_url.format(**context)
    if match := re.match(
        r"^(GET|HEAD|POST|PUT|DELETE|PATCH) (.*)$", maybe_method_and_url
    ):
        return (match[2], match[1])
    return (maybe_method_and_url, None)
