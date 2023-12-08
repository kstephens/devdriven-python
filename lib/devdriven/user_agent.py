import json
import urllib3
from devdriven.url import url_normalize, url_scheme, url_to_str
from devdriven.file_response import FileResponse

class UserAgent():
  http_pool_manager = None

  def __init__(self, headers=None, base_url=None, http_pool_manager=None):
    self.headers = (headers or {})
    self.base_url = url_normalize(base_url)
    self.http_pool_manager = (http_pool_manager or urllib3.PoolManager())

  def __call__(self, *args, **kwargs):
    self.request(*args, **kwargs)

  def request(self, method, url, headers=None, body=None, **kwargs):
    method = method.upper()
    url = url_normalize(url, self.base_url)
    scheme = url_scheme(url)
    if not scheme:
      raise Exception(f"cannot process {url}")
    headers = (self.headers or {}) | (headers or {})
    for key, val in list(headers.items()):
      if val is None:
        del headers[key]
    return getattr(self, f'_request_scheme_{scheme}')(method, url, headers, body, kwargs)

  # pylint: disable-next=too-many-arguments
  def _request_scheme_http(self, method, url, headers, body, kwargs):
    return self.http_pool_manager.request(method, url_to_str(url), headers=headers, body=body, **kwargs)

  # pylint: disable-next=too-many-arguments
  def _request_scheme_file(self, method, url, headers, body, kwargs):
    if json_body := kwargs.get('json'):
      assert not body
      body = json.dumps(json_body).encode()
      headers = {'Content-Type': 'application/json'} | headers
    return FileResponse().request(method, url, headers, body, **kwargs)

