import json
import urllib3
from devdriven.file_response import FileResponse
import yurl

class UserAgent():
  http_pool_manager = None

  def __init__(self, headers=None, base_url=None, http_pool_manager=None):
    self.headers = (headers or {})
    self.base_url = (base_url and yurl.URL(base_url))
    self.http_pool_manager = (http_pool_manager or urllib3.PoolManager())

  def __call__(self, *args, **kwargs):
    self.request(*args, **kwargs)

  def request(self, method, url, headers=None, body=None, **kwargs):
    method = method.upper()
    if isinstance(url, str):
      url = yurl.URL(url)
    if self.base_url:
      url = self.base_url + url
    scheme = self.url_flavor(url)
    headers = (self.headers or {}) | (headers or {})
    for key, val in list(headers.items()):
      if val is None:
        del headers[key]
    return getattr(self, f'_request_scheme_{scheme}')(method, url, headers, body, kwargs)

  # pylint: disable-next=too-many-arguments
  def _request_scheme_http(self, method, url, headers, body, kwargs):
    return self.http_pool_manager.request(method, str(url), headers=headers, body=body, **kwargs)

  # pylint: disable-next=too-many-arguments
  def _request_scheme_file(self, method, url, headers, body, kwargs):
    if json_body := kwargs.get('json'):
      assert not body
      body = json.dumps(json_body).encode()
      headers = {'Content-Type': 'application/json'} | headers
    return FileResponse().request(method, url, headers, body, **kwargs)

  def url_flavor(self, url):
    if url.scheme in ('http', 'https'):
      return 'http'
    if url.userinfo or url.port or url.query or url.fragment:
      raise Exception(f"cannot process {url}")
    if url.scheme in ('', 'file') and not url.host:
      return 'file'
    raise Exception(f"cannot process {url}")
