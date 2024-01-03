from devdriven.cli.options import Options
from dataclasses import dataclass, asdict
from icecream import ic

def test_parse_argv():
  argv = ['-abc', '--flag', '--opt=g', 'h', 'i', '-j']
  o = Options()
  o.parse_argv(argv.copy())
  assert o.argv == argv
  assert list(map(lambda o: o.name, o.opts)) == ['a', 'b', 'c', 'flag', 'opt']
  assert list(map(lambda o: o.value, o.opts)) == [True, True, True, True, 'g']
  assert o.args == ['h', 'i', '-j']

def test_parse_argv_dash():
  argv = ['-abc', '--flag', '--', '--opt=g', 'h', 'i', '-j']
  o = Options()
  o.parse_argv(argv.copy())
  assert o.argv == argv
  assert o.opt('a') == True
  assert o.opt('a', 2) == True
  assert o.opt('b', 3) == True
  assert o.opt('c', 5) == True
  assert o.opt('flag', 7) == True
  assert list(map(lambda o: o.name, o.opts)) == ['a', 'b', 'c', 'flag']
  assert list(map(lambda o: o.value, o.opts)) == [True, True, True, True,]
  assert o.args == ['--opt=g', 'h', 'i', '-j']


def test_parse_argv_dash_in_args():
  argv = ['-abc', '--flag', '--opt=g', 'h', 'i', '-j']
  o = Options()
  o.parse_argv(argv.copy())
  assert o.args == ['h', 'i', '-j']
  assert o.opt('a', 2) == True
  assert o.opt('b', 3) == True
  assert o.opt('c', 3) == True
  assert o.opt('opt', 5) == 'g'
  assert o.opt('x', 7) == 7
  assert o.opt('j', 11) == 11

