import io
import yurl
from devdriven.user_agent import UserAgent

class Content():
  def __init__(self, uri=None, content=None, headers=None):
    self.uri = uri
    self._body = None
    self._content = content
    self.headers = headers

  def __repr__(self):
    return f'Content(uri={self.uri!r}, headers={self.headers!r})'
  def __str__(self):
    return self.content()

  def encode(self, encoding='utf-8'):
    return self.content().encode(encoding)

  def to_dict(self):
    return {'Content', str(self.uri)}

  def content(self):
    if not self._content:
      self._content = self.get_content()
    return self._content

  def readable(self, headers=None):
    return io.BytesIO(self.body(headers=headers))

  def get_content(self, headers=None, encoding=None):
    return self.get_body(headers=headers).decode(encoding or 'utf-8')

  def body(self, headers=None):
    if not self._body:
      self._body = self.get_body(headers=headers)
    return self._body

  def get_body(self, headers=None):
    headers = (self.headers or {}) | (headers or {})
    def do_get(url):
      return UserAgent().request('get', url, headers=headers)
    response = with_http_redirects(do_get, self.uri)
    return response._body

  def put_content(self, body, headers=None):
    headers = (self.headers or {}) | (headers or {})
    def do_put(url, body):
      return UserAgent().request('put', url, body=body, headers=headers)
    with_http_redirects(do_put, self.uri, body)
    return self

# ???: UserAgent already handle redirects:
def with_http_redirects(fun, url, *args, **kwargs):
  next_url = yurl.URL(url)
  max_redirects = kwargs.pop('max_redirects', 10)
  redirects = 0
  while completed := redirects <= max_redirects:
    response = fun(next_url, *args, **kwargs)
    if response.status == 301:
      redirects += 1
      next_url = next_url + response.header['Location']
    else:
      break
  if not completed:
    raise Exception("Too many redirects: {self.uri} : {max_redirects}")
  return response
