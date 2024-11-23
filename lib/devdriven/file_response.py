import os
from io import StringIO, BytesIO, TextIOBase, TextIOWrapper
import sys
import hashlib
import json
from datetime import datetime
from email.utils import formatdate
from http.client import responses
from urllib3 import HTTPHeaderDict
from devdriven.url import url_normalize
from devdriven.util import not_implemented
from devdriven import mime

TEXT_IO_CLASSES = (TextIOBase, TextIOWrapper, StringIO)
DEFAULT_ENCODING = 'utf-8'

# Partially compatable with urllib3.response.HTTPResponse:
class FileResponse():
  default_stdin = default_stdout = None

  def __init__(self):
    self._now = None
    self.request_method = self.url = self.file_path = None
    self.status = self.headers = self._body = None
    self.is_stream = self.is_stdio = None
    self.stdin = self.stdout = None
    self.read_io = self.write_io = None
    self.closed = True
    self.encoding = None
    self.connection = '<<FileResponse.connection : NOT-IMPLEMENTED>>'
    self.retries = '<<FileResponse.retries : NOT-IMPLEMENTED>>'
    self._headers = self._body = None
    self._body_loaded = False
    self.preload_content = None

  # https://stackoverflow.com/questions/865115/how-do-i-correctly-clean-up-a-python-object
  def __del__(self):
    self.close()

  def request(self, method, url, headers, body, **kwargs):
    assert self.status is None
    self.request_method = method.upper()
    self.url = url = url_normalize(url)
    headers = (headers or {}).copy()
    self.stdin = headers.pop("X-STDIN", kwargs.get("stdin", (FileResponse.default_stdin or sys.stdin)))
    self.stdout = headers.pop("X-STDOUT", kwargs.get("stdout", (FileResponse.default_stdout or sys.stdout)))
    self._headers = HTTPHeaderDict(headers)
    if url.path == '-':
      self.is_stream = self.is_stdio = True
    else:
      self.file_path = url.path
    self.status = 599
    self.headers = HTTPHeaderDict({})
    if self.preload_content is None:
      self.preload_content = kwargs.get('preload_content', True)
    self._body_loaded = False
    getattr(self, f"_request_method_{method.lower()}")(body)
    return self

  def close(self):
    if not self.closed:
      if not self.is_stream:
        if self.read_io:
          self.read_io.close()
          self.read_io = None
        if self.write_io:
          self.write_io.close()
          self._etag()
          self.write_io = None
      self.closed = True
      self.release_conn()

  @property
  def data(self):
    if not self._body_loaded and self._body is None:
      self._body_loaded = True
      self._body = self.read()
      self.close()
    return self._body

  def drain_conn(self):
    if self.read_io:
      self.read_io.read()
    return self.close()

  def fileno(self):
    return not_implemented()

  def flush(self):
    if self.write_io and not self.closed:
      self.write_io.flush()
    self._etag()

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
    return self.closed

  def json(self):
    return json.load(self.read().decode(self.encoding or DEFAULT_ENCODING))

  def read(self, amt=None, decode_content=None, cache_content=False):
    assert not decode_content
    assert not cache_content
    if self.read_io is None:
      return b''
    read_buf = self.read_io.read(amt)
    encoding = getattr(self.read_io, 'encoding', None) or self.encoding
    if not encoding and self._needs_encoding(self.read_io):
      encoding = DEFAULT_ENCODING
    if encoding:
      read_buf = read_buf.encode(encoding)
    return read_buf

  def read_chunked(self, amt=None, decode_content=None):
    assert not decode_content
    return self.read_io.read_chunked(amt=amt)

  def readable(self):
    # pylint: disable-next=unneeded-not
    return not not self.read_io

  def readinto(self, buf):
    return self.read_io.readinto(buf)

  def readline(self, size=-1):
    return self.read_io.readline(size=size)

  def release_conn(self):
    self.read_io = self.write_io = None
    self.stdin = self.stdout = None

  def seek(self, offset, whence=0):
    return self.read_io.seek(offset, whence)

  def stream(self, amt=65536, decode_content=None):
    assert not decode_content
    return self.read_io.stream(amt=amt)

  def supports_chunked_reads(self):
    return not_implemented()

  def tell(self):
    if self.read_io:
      return self.read_io.tell()
    if self.write_io:
      return self.write_io.tell()
    return None

  def truncate(self):
    # self.write_io.truncate()
    return not_implemented()

  def writable(self):
    # pylint: disable-next=unneeded-not
    return not not self.write_io

  def write(self, buf):
    if isinstance(buf, bytes):
      encoding = getattr(self.write_io, 'encoding', None) or self.encoding
      if not encoding and self._needs_encoding(self.write_io):
        encoding = DEFAULT_ENCODING
      if encoding:
        buf = buf.decode(encoding)
    return self.write_io.write(buf)

  def writelines(self, lines, /):
    for line in lines:
      self.write(line)

  def _needs_encoding(self, io):
    return isinstance(io, TEXT_IO_CLASSES)

  def _encoding(self, io):
    return self.encoding or io.encoding

  ###############################

  def _request_method_get(self, _body):
    if self.is_stdio:
      self.read_io = self.stdin
      self._start(200)
    else:
      self.open_with_error_handling("rb")
    self._preload()
    return self

  def _request_method_put(self, body):
    if self.is_stdio:
      self.write_io = self.stdout
      self._status_body(201)
    else:
      self.open_with_error_handling("wb")
    if body:
      self.write(body)
    self._preload()
    return self

  def _preload(self):
    if self.preload_content and (not self._body_loaded) and self.read_io:
      self._body_loaded = True
      self._body = self.read()
      self.read_io.close()
      self.read_io = None

  def open_with_error_handling(self, mode, *_args):
    self.status, err = 599, None
    error_status = None
    try:
      if mode == 'rb':
        # pylint: disable-next=consider-using-with
        self.read_io = open(self.file_path, 'rb')
        # ???: Can return multiple shapes?
        # See https://docs.python.org/3/library/mimetypes.html#mimetypes.guess_type
        (content_type, _encoding) = mime.guess_type(self.file_path)
        if content_type:
          self.headers['Content-Type'] = content_type
        self._start(200)
        self._etag()
      else:
        # pylint: disable-next=consider-using-with
        self.write_io = open(self.file_path, 'wb')
        self._start(201)
        self._etag()
        self._status_body(self.status)
      self.closed = False
    except FileNotFoundError as exc:
      error_status, err = 404, exc
    except (PermissionError, OSError) as exc:
      # OSError [Errno 30] Read-only file system
      error_status, err = 403, exc
    if err:
      self._status_body(error_status)
      self.headers['X-Error'] = str(err)
    return self

  def _status_body(self, status):
    self._text_body(status, f'{status} {responses.get(status, "Unknown")}\n')

  def _text_body(self, status, body):
    body = body.encode('utf-8')
    self.read_io = BytesIO(body)
    self._body = body
    self._body_loaded = True
    self._start(status)
    self.headers.update({'Content-Type': 'text/plain',
                         'Content-Length': str(len(body))})

  def _start(self, status):
    self.status = status
    self._now = datetime.now()
    self.headers.update({
      'Date': rfc_1123(self._now),
      'Pragma': 'no-cache',
      'Expires': 'Fri, 01 Jan 1990 00:00:00 GMT',
      'Last-Modified': self.headers.get('Last-Modified', rfc_1123(self._now)),
      'Cache-Control': 'no-store, no-cache, must-revalidate',
      'Server': 'Local FileSystem',
      'X-XSS-Protection': '0',
    })

  def _etag(self):
    if not self.file_path:
      return
    try:
      stat = os.stat(self.file_path)
      self.headers.update({
        'Content-Length': str(stat.st_size),
        'ETag': file_etag(self.file_path, stat),
      })
      time = datetime.fromtimestamp(stat.st_mtime)
      self._last_modified(time)
    except FileNotFoundError:
      return

  def _last_modified(self, time):
    self.headers['Last-Modified'] = rfc_1123(time)

# https://stackoverflow.com/questions/225086/rfc-1123-date-representation-in-python
# https://stackoverflow.com/a/37191167/1141958
def rfc_1123(some_datetime):
  return formatdate(some_datetime.timestamp(), usegmt=True)

def file_etag(path, stat):
  path_hash = hashlib.sha1()
  path_hash.update(f"{path}-{stat.st_dev}-{stat.st_ino}-{stat.st_mtime}-{stat.st_size}".encode('utf-8'))
  return path_hash.hexdigest()
