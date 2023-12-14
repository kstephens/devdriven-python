from urllib.parse import urlparse, urlunparse, urljoin

def url_normalize(url, base_url=None):
  url = url_parse(url)
  if base_url := url_parse(base_url):
    url = url_join(base_url, url)
  return url

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
  return urljoin(url_parse(base), url_parse(url))

def url_to_str(url):
  if isinstance(url, str):
    return url
  return urlunparse(url)
