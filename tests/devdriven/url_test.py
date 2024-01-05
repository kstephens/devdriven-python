from urllib.parse import ParseResult
import devdriven.url as sut
# from icecream import ic

def test_url_normalize():
  assert sut.url_normalize('http://test/path') == \
    ParseResult(scheme='http', netloc='test', path='/path', params='', query='', fragment='')
  assert sut.url_normalize('a') == \
    ParseResult(scheme='', netloc='', path='a', params='', query='', fragment='')
  assert sut.url_normalize('/c/d', 'http://a/b') == \
    ParseResult(scheme='http', netloc='a', path='/c/d', params='', query='', fragment='')

def test_url_join():
  assert sut.url_join('http://test/a/b', 'c/d') == \
    ParseResult(scheme='http', netloc='test', path='/a/c/d', params='', query='', fragment='')
  assert sut.url_join('http://test/a/b', '/c/d') == \
    ParseResult(scheme='http', netloc='test', path='/c/d', params='', query='', fragment='')
  assert sut.url_join('http://test/a/b', '..') == \
    ParseResult(scheme='http', netloc='test', path='/', params='', query='', fragment='')
  assert sut.url_join('http://test/a/b', '../c/d') == \
    ParseResult(scheme='http', netloc='test', path='/c/d', params='', query='', fragment='')

def test_url_parse():
  result = ParseResult(scheme='http', netloc='test', path='/', params='', query='', fragment='')
  assert sut.url_parse('http://test/') == result
  assert sut.url_parse(result) == result

def test_url_is_http():
  assert sut.url_is_http(sut.url_parse('http://test/path')) == 'http'
  assert sut.url_is_http(sut.url_parse('https://test/path')) == 'http'
  assert sut.url_is_http(sut.url_parse('file:///test/path')) is False
  assert sut.url_is_http(sut.url_parse('test/path')) is False

def test_url_is_file():
  assert_map(sut.url_is_file,
             parse_urls(),
             [False, False, False, 'file', 'file', 'file', 'file', 'file'])

def test_url_is_stdio():
  assert_map(sut.url_is_stdio,
             parse_urls(),
             [False, False, False, False, False, False, '-', False])

def test_url_scheme():
  assert_map(sut.url_scheme,
             parse_urls(),
             ['http', 'http', False, 'file', 'file', 'file', 'file', 'file'])

def test_url_and_method():
  assert sut.url_and_method('http://test/') == ('http://test/', None)
  assert sut.url_and_method('GET http://test/') == ('http://test/', 'GET')
  assert sut.url_and_method('GET  http://test/') == (' http://test/', 'GET')
  assert sut.url_and_method('WRONG http://test/') == ('WRONG http://test/', None)

###################

def assert_map(func, actual, expect):
  i = -1
  for inp, exp in zip_default(actual, expect):
    i += 1
    actual = func(inp)
    # ic((input, actual, exp))
    assert actual == exp, f'at {i}: input: {inp!r} actual: {actual!r} expect: {exp!r}'


URLS = [
  'http://a/b',
  'https://a/b',
  'file://a/b',
  'file:///a/b',
  '/a/b',
  '/a',
  '-',
  '',
]

def parse_urls():
  return list(map(sut.url_parse, URLS))

def zip_default(a, b, default=None):
  a = list(a)
  b = list(b)
  max_size = max(len(a), len(b))
  a = expand_to_size(a, max_size, default)
  b = expand_to_size(b, max_size, default)
  return zip(a, b)

def expand_to_size(seq, size, default=None):
  seq = list(seq)
  return seq + [default] * (size - len(seq))
