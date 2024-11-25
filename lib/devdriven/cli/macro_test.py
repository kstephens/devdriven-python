from .macro import MacroExpander

MACROS = {
  'indx': 'b arg1 "$1" $-1 "$2" arg2',
  'glob': 'b arg1 "$*" "before $* after" before$*after arg2',
  'argv': 'b arg1 "$@" "before $@ after" before$@after arg2',
  'all': 'a 1: $1 1q: "$1" 2: $2 2q: "$2" @: $@ @q: "$@" *: $* *q: "$*" rest',
}

def test_expand_indx():
  macros = {'indx': 'b arg1 "$1" $-1 "$2" arg2'}
  subject = MacroExpander(macros=macros)
  cmd = ['indx', 'a', 'b c']
  actual = subject.expand_macro(cmd)
  expect = ['b', 'arg1', 'a', 'b', 'c', 'b c', 'arg2']
  assert actual == expect

def test_expand_glob():
  macros = {'glob': 'b arg1 "$*" "before $* after" before$*after arg2'}
  subject = MacroExpander(macros=macros)
  cmd = ['glob', 'a', 'b c']
  actual = subject.expand_macro(cmd)
  expect = ['b', 'arg1', 'a b c', 'before a b c after', 'beforea', 'b', 'cafter', 'arg2']
  assert actual == expect

def test_expand_argv():
  macros = {'argv': 'b arg1 "$@" "before $@ after" before$@after arg2'}
  subject = MacroExpander(macros=macros)
  cmd = ['argv', 'a', 'b c']
  actual = subject.expand_macro(cmd)
  expect = [
    'b', 'arg1', 'a', 'b c',
    'before a after',
    'before b c after',
    'beforea', 'b', 'cafter',
    'arg2'
  ]
  print(repr(actual))
  assert actual == expect

def test_expand_more():
  macros = {
    'a': 'b "$1" "$*" "$@" "x$2y"',
    'b': 'c x $2 y',
  }
  subject = MacroExpander(macros=macros)
  cmd = ['a', '1', '2 3', '4']
  actual = subject.expand_macro(cmd)
  expect = ['b', '1', '1 2 3 4', '1', '2 3', '4', '2 3']
  assert actual == expect

def test_expand_all():
  macros = {'all': 'a 1: $1 1q: "$1" 2: $2 2q: "$2" @: $@ @q: "$@" *: $* *q: "$*" rest'}
  subject = MacroExpander(macros=macros)
  cmd = ['all', 'a', 'b c']
  actual = subject.expand_macro(cmd)
  expect = [
    'a',
    '1:',
    'a',
    '1q:',
    'a',
    '2:',
    'b',
    'c',
    '2q:',
    'b c',
    '@:',
    'a',
    'b',
    'c',
    '@q:',
    'a',
    'b c',
    '*:',
    'a',
    'b',
    'c',
    '*q:',
    'a b c',
    'rest'
  ]
  assert actual == expect
