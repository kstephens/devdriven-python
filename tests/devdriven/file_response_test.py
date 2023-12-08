from io import StringIO
import os
import contextlib
import sys
from devdriven.user_agent import UserAgent
from devdriven.file_response import FileResponse
from icecream import ic

TEST_FILE = 'tmp/user-agent-test.csv'

def test_file_put_201_create():
  with contextlib.suppress(FileNotFoundError):
    os.remove(TEST_FILE)
  response = file_fut('put', TEST_FILE, body=b'OK\n')
  assert response.status == 201
  assert response.read() == b'201 Created\n'
  assert int(response.headers['Content-Length']) == 12
  assert response.headers['Content-Type'] == 'text/plain'
  assert response.headers['content-type'] == 'text/plain'
  assert 'ETag' in response.headers

def test_file_get_200_created():
  response = file_fut('get', TEST_FILE)
  assert response.status == 200
  assert response._body is None
  body = response.read()
  assert body >= b'OK\n'
  assert response.headers['Content-Type'] == 'text/csv'
  assert 'ETag' in response.headers

def test_file_get_200_created_preload():
  response = file_fut('get', TEST_FILE, preload_content=True)
  assert response.status == 200
  assert response._body >= b'OK\n'
  assert response.read() >= b''
  assert response.headers['Content-Type'] == 'text/csv'
  assert 'ETag' in response.headers

def test_file_put_201_changed():
  response = file_fut('put', TEST_FILE, body=b'CHANGED\n')
  assert response.status == 201
  assert response.read() == b'201 Created\n'
  assert response.headers['Content-Type'] == 'text/plain'
  assert 'ETag' in response.headers

def xtest_file_get_200_changed():
  response = file_fut('get', TEST_FILE)
  assert response.status == 200
  assert 'ETag' in response.headers
  assert response.headers['Content-Type'] == 'text/csv'
  assert response._body >= b'CHANGED\n'

def test_file_get_403_unreadable():
  os.chmod(TEST_FILE, 0)
  response = file_fut('get', '/etc/sudoers')
  assert response.status == 403
  assert response.read() == b'403 Forbidden\n'
  assert response.headers['Content-Type'] == 'text/plain'
  assert 'ETag' not in response.headers

def test_file_get_404_non_existent():
  with contextlib.suppress(FileNotFoundError):
    os.remove(TEST_FILE)
  response = file_fut('get', TEST_FILE)
  assert response.status == 404
  assert response.read() == b'404 Not Found\n'
  assert response.headers['Content-Type'] == 'text/plain'
  assert 'ETag' not in response.headers

def test_file_get_403():
  response = file_fut('get', '/etc/sudoers')
  assert response.status == 403
  assert response.read() == b'403 Forbidden\n'
  assert response.headers['Content-Type'] == 'text/plain'
  assert 'ETag' not in response.headers

def xtest_file_get_stdin():
  test_stdin = StringIO("STDIN\n")
  response = file_fut('get', '-', headers={'X-STDIN': test_stdin})
  assert response.status == 200
  assert response.read() == 'STDIN\n'
  assert 'Content-Type' not in response.headers
  assert 'ETag' not in response.headers

def test_file_put_stdout():
  test_stdout = StringIO()
  response = file_fut('put', '-', headers={'X-STDOUT': test_stdout}, body=b'STDOUT\n')
  assert response.status == 201
  assert response.read() == b'201 Created\n'
  assert response.headers['Content-Type'] == 'text/plain'
  assert 'ETag' not in response.headers
  assert test_stdout.getvalue() == 'STDOUT\n'


def test_http_get_200():
  response = user_agent_fut('get', 'https://github.com/')
  assert response.status == 200
  assert len(response._body) >= 100
  body = response.read()
  assert len(body) == 0
  assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
  assert 'ETag' in response.headers

########################################

def file_fut(method, url, headers=None, body=None, **kwargs):
  sys.stdout.flush()
  sys.stderr.flush()
  kwargs['preload_content'] = kwargs.get('preload_content', False)
  fun = FileResponse().request
  response = assert_response(fun, method, url, headers, body, **kwargs)
  # pprint(response)
  if url != '-':
    response = user_agent_fut(method, url, headers, body, **kwargs)
  sys.stdout.flush()
  sys.stderr.flush()
  return response

def user_agent_fut(method, url, headers=None, body=None, **kwargs):
  return assert_response(UserAgent().request, method, url, headers, body, **kwargs)

def assert_response(fun, method, url, headers, body, **kwargs):
  # pprint((method, url, headers, body))
  response = fun(method, url, headers, body, **kwargs)
  if not 200 <= response.status <= 299:
    assert 'ETag' not in response.headers
    assert 'X-Error' in response.headers
  return response
