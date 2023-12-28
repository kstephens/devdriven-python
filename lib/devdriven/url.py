import re
from typing import Any, Optional, Tuple
from urllib.parse import urlparse, urlunparse, urljoin

def url_normalize(url, base_url=None):
  if base_url:
    url = url_join(base_url, url)
  return url_parse(url)

def url_parse(url):
  if isinstance(url, str):
    url = urlparse(url)
  return url

def url_is_http(url):
  return url.scheme in ('http', 'https') and 'http'

def url_is_file(url):
  if url.netloc or url.query or url.fragment:
    return False
  if url.scheme in ('', 'file') and not url.netloc:
    return 'file'
  return False

def url_is_stdio(url):
  return not url_is_http(url) and url.path == '-' and '-'

def url_scheme(url):
  return url_is_http(url) or url_is_file(url)

def url_join(base, url):
  return urljoin(url_to_str(base), url_to_str(url))

def url_to_str(url):
  if isinstance(url, str):
    return url
  return urlunparse(url)

def url_and_method(maybe_method_and_url: str,
                    context: Any = None) -> Tuple[str, Optional[str]]:
    if context:
        maybe_method_and_url = maybe_method_and_url.format(**context)
    if match := re.match(r'^(GET|HEAD|POST|PUT|DELETE|PATCH) (.*)$', maybe_method_and_url):
        return (match[2], match[1])
    return (maybe_method_and_url, None)

