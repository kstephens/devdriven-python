import devdriven.version as sut
from devdriven.asserts import assert_output, pp_output

VERSION_STRINGS = '''
1.2
1.3.45
1.3.45a
1.3.45ab
1.3.45ab4
1.3.45-ab_4
1.3_45_ab-4'''.split('\n')

def test_parse():
  results = [(inp, sut.parse(inp)) for inp in VERSION_STRINGS]
  assert results == [
    ('', []),
    ('1.2', [1, '.', 2]),
    ('1.3.45', [1, '.', 3, '.', 45]),
    ('1.3.45a', [1, '.', 3, '.', 45, 'a']),
    ('1.3.45ab', [1, '.', 3, '.', 45, 'ab']),
    ('1.3.45ab4', [1, '.', 3, '.', 45, 'ab', 4]),
    ('1.3.45-ab_4', [1, '.', 3, '.', 45, '-', 'ab', '_', 4]),
    ('1.3_45_ab-4', [1, '.', 3, '_', 45, '_', 'ab', '-', 4]),
  ]

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

def assert_pprint(key, data):
  assert_output(f'tests/devdriven/output/version_test/{key}', pp_output(data))
