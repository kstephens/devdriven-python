from pprint import pprint
import os
import contextlib
import yurl
from devdriven.user_agent import UserAgent

TEST_FILE = 'tmp/user-agent-test.csv'

def test_put_201_create():
  with contextlib.suppress(FileNotFoundError):
    os.remove(TEST_FILE)
  status, headers, body = fut('put', TEST_FILE, body=b'OK\n')
  assert status == 201
  assert body == b'201 Created'
  assert headers['Content-Type'] == 'text/plain'
  assert 'ETag' in headers

def test_get_200_created():
  status, headers, body = fut('get', TEST_FILE)
  assert status == 200
  assert body >= b'OK\n'
  assert headers['Content-Type'] == 'text/csv'
  assert 'ETag' in headers

def test_put_201_changed():
  status, headers, body = fut('put', TEST_FILE, body=b'CHANGED\n')
  assert status == 201
  assert body == b'201 Created'
  assert headers['Content-Type'] == 'text/plain'
  assert 'ETag' in headers

def test_get_200_changed():
  status, headers, body = fut('get', TEST_FILE)
  assert status == 200
  assert 'ETag' in headers
  assert headers['Content-Type'] == 'text/csv'
  assert body >= b'CHANGED\n'

def test_get_403_unreadable():
  os.chmod(TEST_FILE, 0)
  status, headers, body = fut('get', '/etc/sudoers')
  assert status == 403
  assert body == b'403 Forbidden'
  assert headers['Content-Type'] == 'text/plain'
  assert 'ETag' not in headers

def test_get_404_non_existent():
  with contextlib.suppress(FileNotFoundError):
    os.remove(TEST_FILE)
  status, headers, body = fut('get', TEST_FILE)
  assert status == 404
  assert body == b'404 Not Found'
  assert headers['Content-Type'] == 'text/plain'
  assert 'ETag' not in headers

def test_get_403():
  status, headers, body = fut('get', '/etc/sudoers')
  assert status == 403
  assert body == b'403 Forbidden'
  assert headers['Content-Type'] == 'text/plain'
  assert 'ETag' not in headers

def test_put_stdout():
  status, headers, body = fut('put', '-', body=b'STDOUT\n')
  assert status == 201
  assert body == b'201 Created'
  assert headers['Content-Type'] == 'text/plain'
  assert 'ETag' not in headers

def fut(method, url, headers=None, body=None):
  url = yurl.URL(url)
  fun = UserAgent.FileResponse().request_tuple
  assert_response(fun, method, url, headers, body)
  fun = UserAgent().request_tuple
  return assert_response(fun, method, url, headers, body)

def assert_response(fun, method, url, headers, body):
  # pprint((method, url, headers, body))
  response = fun(method, url, headers, body)
  # pprint(response)
  status, headers, body = response
  assert int(headers['Content-Length']) == len(body)
  if not 200 <= status <= 299:
    assert 'ETag' not in headers
    assert 'X-Error' in headers
  return response
