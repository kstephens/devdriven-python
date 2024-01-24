from typing import Any, Optional, Iterable, Dict
from abc import ABC, abstractmethod
# from dataclasses import dataclass, field
from pathlib import Path
from devdriven.tempfile import tempfile_from_readable
from devdriven.url import url_normalize, url_join, url_to_str, url_is_file, url_is_stdio, StrOrURL
from devdriven.user_agent import UserAgent
import pandas as pd  # type: ignore


def content_info(headers: dict):
  typ, enc = headers.get('content-type'), headers.get('content-encoding')
  if typ in ('text/plain', 'text/html'):
    return ('text', 'lines', enc)
  # if type in (''):
  #    return ('')
  return (None, None, enc)


class ContentImpl(ABC):
  '''
  Encapsulates data as it passes through Command.xform.
  Subclasses follow this protocol.
  '''

  ###########################################

  @abstractmethod
  def as_str(self) -> str:
    return ''

  @abstractmethod
  def as_bytes(self) -> bytes:
    return b''

  @abstractmethod
  def as_dataframe(self) -> pd.DataFrame:
    return pd.DataFrame({'data': list(self.as_iterable())})

  @abstractmethod
  def as_iterable(self) -> Iterable:
    return [self.as_str()]


class Content:
  _impl: ContentImpl
  _as_str: Optional[str]
  _as_bytes: Optional[bytes]
  _as_dataframe: Optional[pd.DataFrame]
  _as_iterable: Optional[Iterable]

  def __init__(self, impl: ContentImpl):
    self._impl = impl

  @property
  def impl(self) -> ContentImpl:
    return self._impl

  @impl.setter
  def impl(self, value: ContentImpl):
    self._impl = value
    self._as_str = self._as_bytes = None
    self._as_dataframe = self._as_iterable = None

  def as_str(self) -> str:
    if not self._as_str:
      self._as_str = self.impl.as_str()
    return self._as_str

  def as_bytes(self) -> bytes:
    if not self._as_bytes:
      self._as_bytes = self.impl.as_bytes()
    return self._as_bytes

  def as_dataframe(self) -> pd.DataFrame:
    if not self._as_dataframe:
      self._as_dataframe = self.impl.as_dataframe()
    return self._as_dataframe

  def as_iterable(self) -> Iterable:
    return [self.as_str()]


class ContentStr(ContentImpl):
  data: str
  encoding: str

  def as_str(self) -> str:
    return self.data

  def as_bytes(self) -> bytes:
    return self.data.encode(self.encoding or 'utf-8')

  def as_iterable(self) -> Iterable:
    return [self.as_str().splitlines(True)]


class ContentBytes(ContentImpl):
  data: bytes
  encoding: str

  def as_str(self) -> str:
    return self.data.decode(self.encoding or 'utf-8')

  def as_bytes(self) -> bytes:
    return self.data

  def as_iterable(self) -> Iterable:
    return [self.as_str().splitlines(True)]

  def content_encoding(self) -> str:
    return self.encoding


class ContentDataFrame(ContentImpl):
  data: pd.DataFrame

  def as_dataframe(self) -> pd.DataFrame:
    return self.data

  def as_iterable(self) -> Iterable:
    return iter(ContentDataFrame.Iterator(self.data))

  class Iterator():
    df: pd.DataFrame
    iter: object

    def __init__(self, df):
      self.df = df.reset_index()

    def __iter__(self):
      self.iter = self.df.iterrows()
      return self

    def __next__(self):
      _ind, row = self.iter.__next__()
      return row


class ContentURL(ContentImpl):
  url: StrOrURL
  headers: Dict[str, str] = {}
  encoding: Optional[str] = None
  _body: Optional[bytes] = None
  _content: Optional[bytes] = None
  _response: Any = None

  def as_str(self) -> str:
    return self.content()

  def as_bytes(self) -> bytes:
    return self.body()

  def as_iterable(self) -> Iterable:
    res = self.body()
    if enc := self.encoding and res.headers['content-encoding']:
      return self.body().decode(enc).splitlines()
    return [self.body()]

  ###########################################

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

  def set_encoding(self, encoding):
    '''
Sets the expected encoding.
Resets any cached content.
    '''
    self._content = None
    self.encoding = encoding
    return self

  def content(self, encoding=None):
    '''
The decoded body, defaults to utf-8.

    '''
    if encoding and self.encoding != encoding:
      self.set_encoding(encoding)
    if not self._content:
      self._content = self.body().decode(self.encoding or 'utf-8')
    return self._content

  def body(self):
    if not self._body:
      self._body = self.response().read()
      self._response = None
    return self._body

  def body_as_file(self, fun, suffix=None):
    if self.is_file():
      return fun(self.url.path)
    suffix = suffix or Path(self.url.path).suffix
    return tempfile_from_readable(self.response(), suffix, fun)

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
      next_url = url_to_str(url_join(next_url, response.header['Location']))
    else:
      break
  if not completed:
    raise Exception("PUT {self.url} : status {response and response.status} : Too many redirects : {max_redirects}")
  return response
