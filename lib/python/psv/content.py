from devdriven.user_agent import UserAgent

class Content():
  def __init__(self, uri=None, content=None, headers=None):
    self.uri = uri
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

  def get_content(self, headers=None):
    uri, redirects, response = self.uri, 10, None
    headers = (self.headers or {}) | (headers or {})
    while redirects > 0:
      response = UserAgent().request('get', self.uri, headers=headers)
      if response.status == 301:
        uri = uri + response.header['Location']
        redirects =- 1
      else:
        break
    return response._body.decode('utf-8')

  def put_content(self, body, headers=None):
    headers = (self.headers or {}) | (headers or {})
    UserAgent().request('put', self.uri, body=body, headers=headers)
    return self
