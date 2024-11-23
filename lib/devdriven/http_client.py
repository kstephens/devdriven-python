import re
import logging
from typing import Any, Optional, Union, Dict, Tuple
import urllib.request
import urllib.parse
from .to_dict import dump_json
from .util import elapsed_ms

Headers = Dict[str, str]
HttpResult = Dict[str, Any]
Options = Dict[str, Any]
Data = Union[str, bytes, None]

def send_to_url(url: str, data: Data,
                headers: Optional[Headers] = None,
                **options) -> HttpResult:
  if not headers:
    headers = {}
  if options.get('raw', False):
    if isinstance(data, bytes):
      headers = {'Content-Type': 'application/octet-stream'} | headers
    else:
      headers = {'Content-Type': 'text/plain; charset=utf-8'} | headers
      options['req_encoding'] = 'utf-8'
      data = str(data)
  else:
    headers = {'Content-Type': 'application/json; charset=utf-8'} | headers
    options['req_encoding'] = 'utf-8'
    data = dump_json(data, 2)
  return http_post(url, data, headers=headers, **options)

def http_method_url(maybe_method_and_url: str,
                    context: Optional[Dict] = None) -> Tuple[str, Union[str, None]]:
  if context:
    maybe_method_and_url = maybe_method_and_url.format(**context)
  match = re.match(r'^(GET|HEAD|POST|PUT|DELETE|PATCH) (.*)$', maybe_method_and_url)
  if match:
    return (match[2], match[1])
  return (maybe_method_and_url, None)

# pylint: disable=too-many-locals
def http_post(url: str, body: Union[str, bytes],
              headers: Optional[Headers] = None,
              **options) -> HttpResult:
  url, method = http_method_url(url, context=options.get('context'))
  if not method:
    method = options.get('method', 'POST')
  if req_encoding := options.get('req_encoding'):
    req_body = str(body).encode(req_encoding)
  else:
    req_body = bytes(body)  # type: ignore[arg-type]
  req = urllib.request.Request(url, method=method)
  if headers:
    for key, value in headers.items():
      req.add_header(key, str(value))
  req.add_header('Content-Length', str(len(req_body)))
  result = {
    'method': method,
    'url': url,
    'request': {
      'headers': req.headers,
      'body_size': len(req_body),
    }
  }
  msg = f'http_post : req {method} {url} : req {len(req_body)} bytes'
  if options.get('dry_run', False):
    logging.info("DRY-RUN : %s", msg)
    return result | {
      'ok': True,
      'status': None,
      'error': None,
      'dry_run': True,
      'response': {},
    }
  logging.info("%s", msg)
  ((res, error), dt_ms) = elapsed_ms(http_do_request, req, bytes(req_body), options)
  logging.info("%s : res : status %d : body %d bytes : elapsed %.3f ms",
               msg, res['status'], res['body_size'], dt_ms)
  return result | {
    'ok': 200 <= res['status'] and res['status'] < 400,
    'error': error,
    'response': res,
  }

def http_do_request(req: Any, body: bytes, options: Options) -> Tuple[HttpResult, Optional[HttpResult]]:
  res = error = None
  try:
    with urllib.request.urlopen(req, body) as res:
      res = http_build_response(res, options)
  except urllib.error.HTTPError as exc:
    res = http_build_response(exc, options)
    error = {
      'type': exc.__class__.__name__,
      'message': repr(exc),
    }
  return (res, error)

# # type: ignore[return-value]
def http_build_response(res: Any, options: Options) -> HttpResult:
  body = res.read()
  if res_encoding := options.get('res_encoding'):
    body = body.decode(res_encoding)
  return {
    'status': res.status,
    'headers': dict(res.getheaders()),
    'body_size': len(body),
    'body': body,  # could be bytes or str
  }
