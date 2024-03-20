import random
import devdriven.version as sut
from devdriven.asserts import assert_output, pp_output

VERSION_STRINGS = '''
1.2
2.0
1.3.45
1.3.45a
2
1.3.45ab
2.
1.3.45ab4
1.3.45-ab_4
1.3_45_ab-4'''.split('\n')

def test_parse():
  results = [(inp, sut.version_parse_elements(inp)) for inp in VERSION_STRINGS]
  assert results == [
    ('', []),
    ('1.2', [1, '.', 2]),
    ('2.0', [2, '.', 0]),
    ('1.3.45', [1, '.', 3, '.', 45]),
    ('1.3.45a', [1, '.', 3, '.', 45, 'a']),
    ('2', [2]),
    ('1.3.45ab', [1, '.', 3, '.', 45, 'ab']),
    ('2.', [2, '.']),
    ('1.3.45ab4', [1, '.', 3, '.', 45, 'ab', 4]),
    ('1.3.45-ab_4', [1, '.', 3, '.', 45, '-', 'ab', '_', 4]),
    ('1.3_45_ab-4', [1, '.', 3, '_', 45, '_', 'ab', '-', 4]),
  ]

def test_constructor():
  a = sut.Version('1.2')
  b = sut.Version('1.2')
  assert a == b
  assert a == sut.Version(a)

def test_cmp():
  for a in VERSION_STRINGS:
    assert sut.cmp(sut.Version(a), sut.Version(a), '==') == 0
  results = [
    (a, b, sut.cmp(sut.Version(a), sut.Version(b), 'OP'))
    for a in VERSION_STRINGS
    for b in VERSION_STRINGS
    if a != b
  ]
  assert_pprint('test_cmp', results)

def test_sort():
  strings = '''
1.0
2
2.
2.1
2.2.3
2.4.6
2.4.61
2.z23
2.10
2.10.2
'''.strip().split('\n')
  vers = [sut.Version(s) for s in strings]
  random.shuffle(vers)
  vers.sort()
  assert_pprint('test_sort', vers)

def assert_pprint(key, data):
  assert_output(f'tests/devdriven/output/version_test/{key}', pp_output(data))
