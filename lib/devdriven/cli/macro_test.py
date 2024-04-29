from devdriven.cli.macro import MacroExpander
# from icecream import ic

MACROS = {
  'foo': 'bar 1: $1 1q: "$1" 2: $2 2q: "$2" @: $@ @q: "$@" *: $* *q: "$*" rest'
}

def test_expand_macro():
  subject = MacroExpander(macros=MACROS)
  cmd = ['foo', 'a', 'b c']
  actual = subject.expand_macro(cmd)
  expect = [
    'bar',
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
  # ic(actual)
  assert actual == expect
