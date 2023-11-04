import sys
from pathlib import Path
from devdriven.user_agent import UserAgent

class Content():
  def __init__(self, uri):
    self.uri = uri
    self.content = None

  def __repr__(self):
    return f'Content({self.uri!r})'
  def __str__(self):
    return self.get_content()

  def to_dict(self):
    return {'Content', str(self.uri)}

  def get_content(self):
    if not self.content:
      if self.uri == '-':
        self.content = sys.stdin.read().decode('utf-8')
      else:
        self.content = UserAgent().request('GET', self.uri)._body.decode('utf-8')
    return self.content
