from typing import Optional  # Any, , Iterable, Dict
from pathlib import Path
from devdriven.tempfile import tempfile_from_readable
from devdriven.url import url_normalize, url_is_file, url_is_stdio
from devdriven.user_agent import UserAgent, with_http_redirects

class Content():
  '''
  Encapsulates fetching HTTP body, file contents or STDIO.
  content() - the decoded body, defaults to utf-8.
  body() - the bytes of HTTP body or file contents.
  '''
  # pylint: disable-next=too-many-arguments
  def __init__(self, url=None, headers=None, encoding=None, stdin=None, stdout=None):
    self.url = url_normalize(url)
    self.headers = headers or {}
    self._encoding = encoding
    self.stdin, self.stdout = stdin, stdout
    self._body = self._content = self._response = None

  def __repr__(self):
    return f'Content(url={self.url!r})'

  def __str__(self):
    return self.content()

  def to_dict(self):
    return repr(self)

  def is_file(self):
    return url_is_file(self.url)

  def is_stdio(self):
    return url_is_stdio(self.url)

  @property
  def encoding(self) -> Optional[str]:
    return self._encoding

  @encoding.setter
  def encoding(self, encoding: str):
    '''
    Sets the expected encoding.
    Resets any cached content.
    '''
    if self._encoding != encoding:
      self._encoding = encoding
      self._content = None

  def content(self, encoding=None):
    '''
The decoded body, defaults to utf-8.

    '''
    if encoding and self._encoding != encoding:
      self.encoding = encoding
    if not self._content:
      body = self.body()
      self._content = body.decode(self.encoding or 'utf-8')
    return self._content

  def body(self):
    if not self._body:
      self._response = None
      readable = self.body_as_readable()
      try:
        self._body = readable.read()
      finally:
        readable.close()
    return self._body

  def body_as_readable(self):
    # if self.is_file() and not self.is_stdio():
    #   return open(self.url.path, 'rb')
    return self.response()

  def body_as_file(self, fun, suffix=None):
    if self.is_file() and not self.is_stdio():
      return fun(self.url.path)
    suffix = suffix or Path(self.url.path).suffix
    return tempfile_from_readable(self.body_as_readable(), suffix, fun)

  def response(self):
    if self._response:
      return self._response

    def do_get(url):
      return UserAgent().request('get', url,
                                 headers=self.headers,
                                 preload_content=False,
                                 stdin=self.stdin,
                                 stdout=self.stdout)

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
      return UserAgent().request('put', url,
                                 body=body,
                                 headers=headers,
                                 stdin=self.stdin,
                                 stdout=self.stdout)

    self._response = with_http_redirects(do_put, self.url, body)
    if not 200 <= self._response.status <= 299:
      raise Exception("PUT {url} : unexpected status : {self._response.status}")
    return self
