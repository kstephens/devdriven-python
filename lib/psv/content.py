# from pathlib import Path
# from tempfile import NamedTemporaryFile
from devdriven.url import url_normalize, url_join  # , url_is_file, url_is_stdio
from devdriven.user_agent import UserAgent

class Content():
  def __init__(self, url=None, headers=None, encoding=None):
    self.url = url_normalize(url)
    self.headers = headers or {}
    self.encoding = encoding
    self._body = None
    self._content = None
    self._response = None

  def __repr__(self):
    return f'Content(url={self.url!r})'

  def __str__(self):
    return self.content()

  def to_dict(self):
    return repr(self)

  def set_encoding(self, encoding):
    self._content = None
    self.encoding = encoding
    return self

  def content(self):
    if not self._content:
      self._content = self.body().decode(self.encoding or 'utf-8')
    return self._content

  def body(self):
    if not self._body:
      self._body = self.response().read()
      self._response = None
    return self._body

  def response(self):
    if self._response:
      return self._response

    def do_get(url):
      return UserAgent().request('get', url, headers=self.headers, preload_content=False)

    response = with_http_redirects(do_get, self.url)
    if not response.status == 200:
      raise Exception(f'GET {self.url} : status {response.status}')
    self._response = response
    return response

  def put(self, body, headers=None):
    if isinstance(body, str):
      body = body.encode(self.encoding or 'utf-8')
    headers = self.headers | (headers or {})

    def do_put(url, body):
      return UserAgent().request('put', url, body=body, headers=headers)

    self._response = with_http_redirects(do_put, self.url, body)
    if not 200 <= self._response.status <= 299:
      raise Exception("{url} : unexpected status : {self._response.status}")
    return self

# ???: UserAgent already handle redirects:
def with_http_redirects(fun, url, *args, **kwargs):
  next_url = url_normalize(url)
  max_redirects = kwargs.pop('max_redirects', 10)
  redirects = 0
  while completed := redirects <= max_redirects:
    response = fun(next_url, *args, **kwargs)
    if response.status == 301:
      redirects += 1
      next_url = url_join(next_url, response.header['Location'])
    else:
      break
  if not completed:
    raise Exception("PUT {self.url} : status {response and response.status} : Too many redirects : {max_redirects}")
  return response
