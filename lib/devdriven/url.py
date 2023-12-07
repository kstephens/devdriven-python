import yurl

def url_normalize(url, base_url=None):
  if isinstance(url, str):
    url = yurl.URL(url)
  if base_url:
    if isinstance(base_url, str):
      base_url = yurl.URL(base_url)
    url = base_url + url
  return url

def url_is_http(url):
  return url.scheme in ('http', 'https') and 'http'

def url_is_file(url):
  if url.userinfo or url.port or url.query or url.fragment:
    return False
  if url.scheme in ('', 'file') and not url.host:
    return 'file'
  return False

def url_scheme(url):
  return url_is_http(url) or url_is_file(url)
