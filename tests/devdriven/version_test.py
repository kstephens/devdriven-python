import random
import devdriven.version as sut
from devdriven.asserts import assert_output, open_output, lines_output
from icecream import ic

VERSION_STRINGS = '''
1
1.0
1.2
1.3.45
1.3.45a
1.3.45ab
1.3.45ab4
1.3.45-ab_4
1.3_45_ab-4
2
2.
2.0
2.1
2.1.2
'''.strip().split('\n')

def test_parse():
  results = [(inp, '--->', sut.version_parse_elements(inp)) for inp in VERSION_STRINGS]
  assert_data('test_parse', results)

def test_constructor():
  a = sut.Version('1.2')
  b = sut.Version('1.2')
  assert a == b
  assert a == sut.Version(a)

def test_cmp():
  for a in VERSION_STRINGS:
    assert sut.Version(a).cmp(sut.Version(a), '==') == 0
  results = [
    (a, b, '--->', sut.Version(a).cmp(sut.Version(b), 'OP'))
    for a in VERSION_STRINGS
    for b in VERSION_STRINGS
    if a != b
  ]
  assert_data('test_cmp', results)

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
  assert_data('test_sort', vers)

def test_cmp_list_right():
  # for a in VERSION_STRINGS:
    # assert sut.Version(a).cmp_right(sut.Version(a), '==') == 0
  def elems(a):
    return sut.Version(a).elems
  results = [
    (a, b, '--->', sut.cmp_list_right(elems(a), elems(b)))
    for b in VERSION_STRINGS
    for a in VERSION_STRINGS
    if len(a) >= len(b)
  ]
  results.sort(key=lambda x: x[-1])
  result_file = assert_data('test_cmp_list_right', results)
  # with open(result_file, encoding='utf-8') as io:
  #  print(io.read())

def test_constraint():
  versions = '1.0 1.0.1 2.0 2.1 2.1.3 2.2'.split(' ')
  operators = list(sut.PREDICATE_FOR_OP.keys())
  result = [(op, ver, '--->', sut.parse_version_constraint(f'{op}{ver}')) for op in operators for ver in versions]
  assert_data('test_constraint_parse', result)

  for ver in versions:
    assert sut.VersionConstraintRelation(f'=={ver}')(sut.Version(ver)) is True
    assert sut.VersionConstraintRelation(f'!={ver}')(sut.Version(ver)) is False
  results = [
    (checkbox(sut.VersionConstraintRelation(f'{op}{v2}')(sut.Version(v1))),
     v1, op, v2)
    for op in operators + ['=']
    for v1 in versions
    for v2 in versions
    if not (op in ('==', '!=') and v1 == v2)
  ]
  assert_data('test_constraint_relation_eval', results)

  relations = [
    f'{op}{v2}'
    for op in operators
    for v2 in versions
  ]
  constraints = [
    # (rel1, f'{rel1}, {rel2}')
    f'{rel1}, {rel2}'
    for rel1 in relations
    for rel2 in relations
  ]
  constraints = [sut.VersionConstraint(c) for c in constraints]
  results = [
    [checkbox(co(sut.Version(v1))), v1, str(co)]
    for co in constraints
    for v1 in versions
  ]
  assert_data('test_constraint_eval', results)

def assert_data(key, data):
  return assert_output(f'tests/devdriven/output/version_test/{key}', open_output(lines_output(data)))

def checkbox(x):
  if x:
    return '[x]'
  else:
    return '[ ]'
