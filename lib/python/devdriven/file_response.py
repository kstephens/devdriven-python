import os
import sys
import hashlib
import json
import mimetypes
import logging
from datetime import datetime
from email.utils import formatdate
from http.client import responses
from urllib3 import HTTPHeaderDict
from devdriven.util import not_implemented

# Partially compatable with urllib3.response.HTTPResponse:
class FileResponse():
  default_stdin = default_stdout = None

  def __init__(self):
    self.request_method = self.url = self.file_path = self.is_stream = None
    self.status = self.headers = self._body = None
    self._io = self.read_io = self.write_io = None
    self.closed = True
    self.encoding = 'utf-8'

  # https://stackoverflow.com/questions/865115/how-do-i-correctly-clean-up-a-python-object
  def __del__(self):
    if self._io and not self.closed:
      self.close()

  def request(self, method, url, headers, body):
    self.request_method = method.upper()
    self.url = url
    self.file_path = url.path
    self.is_stream = self.file_path == '-'
    headers = (headers or {}).copy()
    self.read_io = headers.pop("X-STDIN", (FileResponse.default_stdin or sys.stdin))
    self.write_io = headers.pop("X-STDOUT", (FileResponse.default_stdout or sys.stdout))
    self.headers = HTTPHeaderDict(headers)

    self.connection = '<<FileResponse.connection : NOT-IMPLEMENTED>>'
    self.data = b'<<FileResponse.data : NOT-IMPLEMENTED>>'
    self.retries = '<<FileResponse.retries : NOT-IMPLEMENTED>>'
    getattr(self, f"_request_method_{method.lower()}")(body)
    return self

  def close(self):
    if self._io and not self.closed:
      self.closed = True
      if not self.is_stream:
        logging.info("FileResponse.close()")
        # self._io.close()
      self._io = None
    return None
  def connection(self):
    return not_implemented()
  def data(self):
    return not_implemented()
  def drain_conn(self):
    return not_implemented()
  def fileno(self):
    return not_implemented()
  def flush(self):
    return not_implemented()
  def get_redirect_location(self):
    return not_implemented()
  def getheader(self, name, default=None):
    return self.headers.get(name, default)
  def getheaders(self):
    return self.headers
  def geturl(self):
    return str(self.url)
  def info(self):
    return self.headers  # ???
  def isatty(self):
    return not_implemented()
  def isclosed(self):
    return not_implemented()
  def json(self):
    return json.loads(self._body)
  def read(self, amt=None, decode_content=None, cache_content=False):
    return not_implemented()
  def read_chunked(self, amt=None, decode_content=None):
    return not_implemented()
  def readable(self):
    return not_implemented()
  def readinto(self, b):
    return not_implemented()
  def readline(self, size=-1, /):
    return not_implemented()
  def release_conn(self):
    return not_implemented()
  def seek(self, offset, whence=0, /):
    return not_implemented()
  def stream(self, amt=65536, decode_content=None):
    return not_implemented()
  def supports_chunked_reads(self):
    return not_implemented()
  def tell(self):
    return not_implemented()
  def truncate(self):
    return not_implemented()
  def writable(self):
    return not_implemented()
  def writelines(lines, /):
    return not_implemented()

  ###############################

  def _request_method_get(self, _body):
    self.open_with_error_handling("rb", self.read_io, self.read_file)
    return self

  def _request_method_put(self, body):
    self.open_with_error_handling("wb", self.write_io, self.write_file, body)
    return self

  def read_file(self, io):
    if self.is_stream:
      return self.complete(200, {}, io.read().encode(self.encoding))
    body = io.read()
    # ???: Can return multiple shapes?
    # See https://docs.python.org/3/library/mimetypes.html#mimetypes.guess_type
    (content_type, _encoding) = mimetypes.guess_type(self.file_path)
    return self.complete(200, {'Content-Type': content_type}, body)

  def write_file(self, io, body):
    assert not isinstance(io, str)
    if self.is_stream:
      if isinstance(body, bytes):
        body = body.decode(self.encoding)
    io.write(body)
    return self.status_body(201, {})

  def open_with_error_handling(self, mode, io, fun, *args):
    status, headers, body, err = 599, {}, b'', None
    result = None
    try:
      if self.is_stream:
        self._io = io
        result = fun(io, *args)
        self._io = None
      else:
        with open(self.file_path, mode) as io:
          self._io = io
          (status, headers, body) = fun(io, *args)
          self._io = None
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
    finally:
      self._io = None
    if err:
      headers['X-Error'] = str(err)
      result = self.status_body(status, headers)
    self.status, self.headers, self._body = result

  def status_body(self, status, headers):
    return self.text_body(status, headers,
                          f'{status} {responses.get(status, "Unknown")}')

  def text_body(self, status, headers, body):
    return self.complete(status,
                          headers | {'Content-Type': 'text/plain'},
                          body.encode('utf-8'))

  def complete(self, status, headers, body):
    now = datetime.now()
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
    return (status, HTTPHeaderDict(self.headers | basic_headers | headers), body)


# https://stackoverflow.com/questions/225086/rfc-1123-date-representation-in-python
# https://stackoverflow.com/a/37191167/1141958
def rfc_1123(some_datetime):
  return formatdate(some_datetime.timestamp(), usegmt=True)

def file_mtime_datetime(path):
  return datetime.fromtimestamp(os.stat(path).st_mtime)

def file_etag(path):
  stat = os.stat(path)
  path_hash = hashlib.sha1()
  path_hash.update(f"{path}-{stat.st_dev}-{stat.st_ino}-{stat.st_mtime}-{stat.st_size}".encode('utf-8'))
  return path_hash.hexdigest()
