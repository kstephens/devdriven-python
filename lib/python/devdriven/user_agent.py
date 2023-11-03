import os
import sys
import hashlib
import mimetypes
from datetime import datetime
from email.utils import formatdate
from http.client import responses
import urllib3
import yurl

class UserAgent():
  def __init__(self, headers=None, base_url=None, http=None):
    self.headers = (headers or {})
    self.base_url = (base_url and yurl.URL(base_url))
    self.http = (http or urllib3.PoolManager())

  def __call__(self, *args, **kwargs):
    self.request(*args, **kwargs)

  def request(self, method, url, headers=None, body=None):
    method = method.upper()
    if isinstance(url, str):
      url = yurl.URL(url)
    if self.base_url:
      url = self.base_url + url
    scheme = self.url_flavor(url)
    headers = (self.headers or {}) | (headers or {})
    return getattr(self, f'request_{scheme}')(method, url, headers, body)

  def request_tuple(self, method, url, headers=None, body=None):
    result = self.request(method, url, headers=headers, body=body)
    return (result.status, result.headers, result._body)

  def request_http(self, method, url, headers, body):
    return self.http.request(method, str(url), headers=headers, body=body)

  def request_file(self, method, url, headers, body):
    return UserAgent.FileResponse().request(method, url, headers, body)

  def url_flavor(self, url):
    if url.scheme in ('http', 'https'):
      return 'http'
    if url.userinfo or url.port or url.query or url.fragment:
      raise Exception(f"cannot process {url}")
    if url.scheme in ('', 'file') and not url.host:
      return 'file'
    raise Exception(f"cannot process {url}")

  class FileResponse():
    def __init__(self):
      self.method = self.url = self.file_path = self.is_stdio = None
      self.status = self.headers = self._body = None
      self.encoding = 'utf-8'

    def request_tuple(self, method, url, headers=None, body=None):
      self.request(method, url, headers, body)
      return (self.status, self.headers, self._body)

    def request(self, method, url, headers=None, body=None):
      self.method = method.upper()
      self.url = url
      self.file_path = url.path
      self.stdin = sys.stdin
      self.stdout = sys.stdout
      self.is_stdio = self.file_path == '-'
      # TODO: Use urllib3 Header data type.
      self.headers = (headers or {})
      getattr(self, f"method_{method.lower()}")(body)
      return self

    def method_get(self, _body):
      self.open_with_error_handling("rb", self.read_file)
      return self

    def method_put(self, body):
      self.open_with_error_handling("wb", self.write_file, body)
      return self

    def read_file(self, file):
      if self.is_stdio:
        body = self.stdin.read().encode(self.encoding)
      else:
        body = file.read()
      # ???: Can return multiple shapes?
      # See https://docs.python.org/3/library/mimetypes.html#mimetypes.guess_type
      (type, _encoding) = mimetypes.guess_type(self.file_path)
      header = {
        'Content-Type': type,
      }
      return self.complete(200, header, body)

    def write_file(self, file, body):
      if self.is_stdio:
        assert file is None
        if isinstance(body, bytes):
          body = body.decode(self.encoding)
        self.stdout.write(body)
      else:
        file.write(body)
      return self.status_body(201, {})

    def open_with_error_handling(self, mode, fun, *args):
      status, headers, body, err = 599, {}, b'', None
      result = None
      try:
        if self.is_stdio:
          result = fun(None, *args)
        else:
          with open(self.file_path, mode) as file:
            (status, headers, body) = fun(file, *args)
          headers = headers | {
            'Last-Modified': rfc_1123(file_mtime_datetime(self.file_path)),
            'ETag': file_etag(self.file_path),
          }
          result = (status, headers, body)
      except FileNotFoundError as exc:
        status, err = 404, exc
      except (PermissionError, OSError) as exc:
        ## OSError [Errno 30] Read-only file system
        status, err = 403, exc
      if err:
        headers['X-Error'] = str(err)
        result = self.status_body(status, headers)
      self.status, self.headers, self._body = result

    def status_body(self, status, headers):
      return self.body_text_plain(
          status,
          headers,
          f'{status} {responses.get(status, "Unknown")}',
        )

    def body_text_plain(self, status, headers, body):
      return self.complete(status,
                            headers | {'Content-Type': 'text/plain'},
                            body.encode('utf-8'))

    def complete(self, status, headers, body):
      now = datetime.now()
      # Use a HTTPHeaderDict...
      # See https://google.com
      basic_headers = {
        'Date': rfc_1123(now),
        'Pragma': 'no-cache',
        'Expires': 'Fri, 01 Jan 1990 00:00:00 GMT',
        'Last-Modified': headers.get('Last-Modified', rfc_1123(now)),
        'Cache-Control': 'no-store, no-cache, must-revalidate',
        # 'Content-Encoding': self.encoding,
        # 'Content-Type': 'text/html',
        'Server': 'Local FileSystem',
        'Content-Length': str(len(body)),
        'X-XSS-Protection': '0',
      }
      return (status, self.headers | basic_headers | headers, body)


# https://stackoverflow.com/questions/225086/rfc-1123-date-representation-in-python
# https://stackoverflow.com/a/37191167/1141958
def rfc_1123(some_datetime):
  return formatdate(some_datetime.timestamp(), usegmt=True)

def file_mtime_datetime(path):
  return datetime.fromtimestamp(os.stat(path).st_mtime)

def file_etag(path):
  stat = os.stat(path)
  path_hash = hashlib.sha1()
  path_hash.update(f"{path}-{stat.st_dev}-{stat.st_ino}-{stat.st_mtime}".encode('utf-8'))
  return path_hash.hexdigest()
