import sys
from pathlib import Path
from devdriven.user_agent import UserAgent

class Content():
  def __init__(self, uri):
    self.uri = uri
    self._content = None

  def __repr__(self):
    return f'Content({self.uri!r})'
  def __str__(self):
    return self.content()

  def to_dict(self):
    return {'Content', str(self.uri)}

  def content(self):
    if not self._content:
      self._content = self.get_content()
    return self._content

  def get_content(self):
    uri, redirects, response = self.uri, 10, None
    while redirects > 0:
      response = UserAgent().request('GET', self.uri)
      ic(response.url)
      ic(response.status)
      ic(response.headers)
      ic(response._body)
      if response.status == 307:
        uri = uri + response.header['Location']
        redirects =- 1
      else:
        break
    return response._body.decode('utf-8')

  def put_content(self, body):
    self.content = body
    UserAgent().request('PUT', self.uri, body=body)
    return self
