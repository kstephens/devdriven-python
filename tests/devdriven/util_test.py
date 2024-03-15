import subprocess
import time
import re
from devdriven import util  # type: ignore

def test_maybe_decode_bytes():
  assert util.maybe_decode_bytes(b'A') == 'A'
  assert util.maybe_decode_bytes(b'\xff') is None
  assert util.maybe_decode_bytes(None) is None

def test_exec_command():
  result = util.exec_command(['echo', 'OK'])
  assert result.returncode == 0
  assert result.stdout is None
  assert result.stderr is None

  result = util.exec_command(['echo', 'OK'],
                             capture_output=True)
  assert result.returncode == 0
  assert result.stdout == b'OK\n'
  assert result.stderr == b''

  result = util.exec_command(['echo ERROR >&2'],
                             capture_output=True, shell=True)
  assert result.returncode == 0
  assert result.stdout == b''
  assert result.stderr == b'ERROR\n'

  ex = None
  try:
    util.exec_command(['false'], check=True)
  except subprocess.CalledProcessError as err:
    ex = err
  assert ex is not None

def test_partition():
  assert util.partition(['a', 1, 'b', 2], lambda e: isinstance(e, str)) == (['a', 'b'], [1, 2])

def test_map_partition():
  assert util.map_partition(lambda x: x % 3, range(1, 9)) == {1: [1, 4, 7], 2: [2, 5, 8], 0: [3, 6]}

def test_frequency():
  assert util.frequency(['a', 1, 'a', 2]) == {'a': 2, 1: 1, 2: 1}

def test_uniq_by():
  assert util.uniq_by([['a', 1], ['b', 2], ['a', 2]], key=lambda e: e[0]) == [['a', 1], ['b', 2]]

def test_parse_commands():
  assert not util.parse_commands([])
  assert util.parse_commands(['cmd1']) == \
    [['cmd1']]
  assert util.parse_commands(['cmd1', 'a']) == \
    [['cmd1', 'a']]
  assert util.parse_commands(['cmd1', 'a', 'b', ',', 'cmd2', 'c']) == \
    [['cmd1', 'a', 'b'], ['cmd2', 'c']]
  assert util.parse_commands(['cmd1', 'a', 'b,', 'cmd2', 'c']) == \
    [['cmd1', 'a', 'b'], ['cmd2', 'c']]
  assert util.parse_commands(['cmd1', 'a', 'b;;', 'cmd2', 'c'], r'^(.*);$') == \
    [['cmd1', 'a', 'b;'], ['cmd2', 'c']]

##########################################################

def test_splitkeep():
  def fut(inp, sep='|'):
    return util.splitkeep(inp, sep)
  assert fut('') == []
  assert fut('abc') == ['abc']
  assert fut('abc|') == ['abc|']
  assert fut('abc||') == ['abc|', '|']
  assert fut(b'', b'|') == []
  assert fut(b'abc', b'|') == [b'abc']
  assert fut(b'abc|', b'|') == [b'abc|']
  assert fut(b'abc||', b'|') == [b'abc|', b'|']


##########################################################

def test_elapsed_ms():
  result, dt_ms = util.elapsed_ms(take_some_time, 2, arg2=3)
  assert result == 6
  assert dt_ms >= 50

def test_elapsed_ms_exception():
  result, dt_ms, exc = util.elapsed_ms_exception(Exception, take_some_time, 2, arg2=3)
  assert result == 6
  assert dt_ms >= 50
  assert exc is None

  kwargs = {'arg3': 11}
  result, dt_ms, exc = util.elapsed_ms_exception(Exception, take_some_time_and_raise, 5, arg2=7, **kwargs)
  assert result is None
  assert dt_ms >= 70
  assert isinstance(exc, Exception)

def take_some_time(arg1, arg2=9):
  assert arg1 == 2
  assert arg2 == 3
  time.sleep(0.050)
  return 1 + arg1 + arg2

def take_some_time_and_raise(arg1, arg2=9, arg3=11):
  assert arg1 == 5
  assert arg2 == 7
  assert arg3 == 11
  time.sleep(0.070)
  raise Exception()

##########################################################

def test_parse_range():
  n = 23
  assert util.parse_range("", n) is None
  assert util.parse_range(":", n) == range(0, n, 1)
  assert util.parse_range("::", n) is None
  assert util.parse_range("::5", n) == range(0, n, 5)
  assert util.parse_range("2:10", n) == range(2, 10, 1)
  assert util.parse_range(":10", n) == range(0, 10, 1)
  assert util.parse_range("2:", n) == range(2, n, 1)
  assert util.parse_range(":5", n) == range(0, 5, 1)
  assert util.parse_range("-5:", n) == range(18, 23, 1)
  assert util.parse_range(":-3", n) == range(0, 20, 1)
  assert util.parse_range("-5:-2", n) == range(18, 21, 1)
  assert util.parse_range("-2:-5", n) == range(21, 18, -1)
  assert util.parse_range("2:10:3", n) == range(2, 10, 3)

def test_glob_to_rx():
  def fut(glob, path, **args):
    rx = util.glob_to_rx(glob, **args)
    return re.match(rx, path) is not None
  assert fut('', '') is True
  assert fut('.', '') is False
  assert fut('.', 'x') is True
  assert fut('.', '.') is True
  assert fut('.', '/') is False
  assert fut('a.', 'a.') is True
  assert fut('a.*', 'a.') is True
  assert fut('a.*', 'a.b') is True
  assert fut('a.*', 'a.bc') is True
  assert fut('*.', 'a.') is True
  assert fut('*.*', 'a.') is True
  assert fut('*.*', 'a.b') is True
  assert fut('*.*', 'a.bc') is True
  assert fut('a/b.c', '*.c') is False
  assert fut('a/b.c', 'a/b.c') is True
  assert fut('*/b.c', 'a/b.c') is True
  assert fut('a*/b.c', 'a/b.c') is True
  assert fut('a*/b.c', 'x/b.c') is False
  assert fut('a*/b.c', '/b.c') is False
  assert fut('d/a*/b.c', 'ad/b.c') is False
  assert fut('d/a*/b.c', 'd/a/b.c') is True

def test_wrap_word():
  def fut(words):
    return util.wrap_words(words, 20)
  assert fut('a b c d') == ['a b c d']
  assert fut(' a  b c d ') == [' a  b c d ']
  assert fut('some very long sentence with punctuation.  And more. ') == [
    'some very long sentence ',
    'with punctuation.  And ',
    'more. '
  ]
  assert fut('some-very-long-word-with-punctuation.  And more.') == [
    'some-very-long-word-with-punctuation.',
    '  And more.'
  ]
