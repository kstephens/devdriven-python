from typing import Any, Optional, Union, Callable, Tuple
from collections.abc import Sequence
import re

VersionElements = Sequence[Union[int, str]]

def version(x):
  return Version(x)

def constraint(x):
  return VersionConstraint(x)


class Version:
  elems: tuple
  _str: str
  _repr: str

  def __init__(self, other: Any):
    if isinstance(other, Version):
      ver: Version = other
      self._str = ver._str
      self._repr = ver._repr
      self.elems = ver.elems
      return
    self._str = str(other).strip()
    self._repr = f'{type(self).__name__}({self._str!r})'
    self.elems = tuple(version_parse_elements(self._str))

  def __str__(self) -> str:
    return self._str

  def __repr__(self) -> str:
    return self._repr

  def __eq__(self, other) -> bool:
    return self._str == typecheck_op(self, other, '==')._str

  def __ne__(self, other) -> bool:
    return self._str != typecheck_op(self, other, '!=')._str

  def __le__(self, other) -> bool:
    other = typecheck_op(self, other, '<=')
    return self._str == other._str or self.cmp(other, '<=') <= 0

  def __ge__(self, other) -> bool:
    other = typecheck_op(self, other, '>=')
    return self._str == other._str or self.cmp(other, '>=') >= 0

  def __lt__(self, other) -> bool:
    return self.cmp(other, '<') < 0

  def __gt__(self, other) -> bool:
    return self.cmp(other, '>') > 0

  def cmp(self, other: Any, op_name: str) -> int:
    # pylint: disable-next=protected-access
    return cmp_list(self.elems, typecheck_op(self, other, op_name).elems)

  def cmp_right(self, other: Any, op_name: str) -> int:
    return cmp_list_right(self.elems, typecheck_op(self, other, op_name).elems)

CoerceableVersion = Union[Version, str]

def typecheck_op(self: Version, other: CoerceableVersion, name: str) -> Any:
  if ver := convert_to_version(other):
    return ver
  raise TypeError(f'{name} not supported between instances of '
                  f'{type(self).__name__!r} and {type(other).__name__!r} : '
                  f'({self!r}) {name} {other!r}')

def coerce_to_version(other: CoerceableVersion) -> Version:
  if ver := convert_to_version(other):
    return ver
  raise TypeError(f'cannot coerce to Version : {type(other).__name__} : {other!r}')

def convert_to_version(ver: Any) -> Optional[Version]:
  if isinstance(ver, Version):
    return ver
  if isinstance(ver, str):
    return Version(ver)
  return None



VERSION_PARSE_ELEMENTS_RX = re.compile(r'(\d+)|([a-zA-Z]+)|([^\da-zA-Z]+)')

def version_parse_elements(ver: str) -> VersionElements:
  return [int(m[1]) if m[1] else (m[2] or m[3]) for m in re.finditer(VERSION_PARSE_ELEMENTS_RX, ver)]

def cmp_list(a: VersionElements, b: VersionElements) -> int:
  for i in range(max(len(a), len(b))):
    if i >= len(a) or i >= len(b):
      break
    if (result := cmp_elem(a[i], b[i])) != 0:
      return result
  return cmp_elem(len(a), len(b))

def cmp_list_right(a: VersionElements, b: VersionElements) -> int:
  for i in range(len(b)):
    if i >= len(a):
      break
    if i >= len(b) - 1:
      return cmp_elem(a[i], b[i])
    if (result := cmp_elem(a[i], b[i])) != 0:
      return result
  return cmp_elem(len(a), len(b))

def cmp_elem(a: Any, b: Any) -> int:
  # pylint: disable-next=unidiomatic-typecheck
  if type(a) == type(b):
    return cmp_same(a, b)
  return cmp_same(str(a), str(b))

def cmp_same(a: Any, b: Any) -> int:
  if a > b:
    return 1
  if a < b:
    return -1
  return 0


class VersionConstraintRelation:
  op: str
  version: Version
  _str: str
  _repr: str
  _pred: Callable[[Version, Version], bool]

  def __init__(self, other: Any):
    if isinstance(other, VersionConstraintRelation):
      vcr: VersionConstraintRelation = other
      self._str = vcr._str
      self._repr = vcr._repr
      self.op, self.version = vcr.op, vcr.version
      self._pred = vcr._pred
      return
    self._str = str(other).strip().replace(' ', '')
    self._repr = f'{type(self).__name__}({self._str!r})'
    self.op, self.version = parse_version_constraint(self._str)
    self._pred = PREDICATE_FOR_OP[self.op]

  def __call__(self, version: Version) -> bool:
    version = coerce_to_version(version)
    return self._pred(version, self.version)

  def match(self, version: Version) -> bool:
    return self._pred(version, self.version)

  def __str__(self) -> str:
    return self._str

  def __repr__(self) -> str:
    return self._repr


PREDICATE_ALIAS = {
  '=': '==',
  '!': '!=',
  '~!': '~!=',
}
PREDICATE_FOR_OP = {
  '==': lambda a, b: a == b,
  '!=': lambda a, b: a != b,
  '<': lambda a, b: a < b,
  '>': lambda a, b: a > b,
  '<=': lambda a, b: a <= b,
  '>=': lambda a, b: a >= b,
  '~=': lambda a, b: a.cmp_right(b, '~=') == 0,
  '~!=': lambda a, b: a.cmp_right(b, '~!=') != 0,
  '~<': lambda a, b: a.cmp_right(b, '~<') < 0,
  '~>': lambda a, b: a.cmp_right(b, '~>') > 0,
  '~<=': lambda a, b: a.cmp_right(b, '~<=') <= 0,
  '~>=': lambda a, b: a.cmp_right(b, '~>=') >= 0,
}
PREDICATE_OPS = list(reversed(sorted(list(PREDICATE_FOR_OP.keys()) + list(PREDICATE_ALIAS.keys()), key=len)))
PREDICATE_OPS_RX = f'({"|".join(PREDICATE_OPS)})'
VERSION_CONSTRAINT_ELEMENT_RX = re.compile(f'^\\s*{PREDICATE_OPS_RX}\\s*(({VERSION_PARSE_ELEMENTS_RX.pattern})+)\\s*$')

def parse_version_constraint(constraint: str) -> Tuple[str, Version]:
  if m := re.match(VERSION_CONSTRAINT_ELEMENT_RX, constraint):
    return (PREDICATE_ALIAS.get(m[1], m[1]), Version(m[2]))
  raise TypeError(f'VersionConstraint: cannot parse {constraint!r}')


class VersionConstraint:
  _str: str
  _repr: str
  _preds: Tuple[VersionConstraintRelation, ...]

  def __init__(self, other: Any):
    if isinstance(other, VersionConstraint):
      vc: VersionConstraint = other
      self._str = vc._str
      self._repr = vc._repr
      self._preds = vc._preds
      return
    self._str = str(other).strip().replace(' ', '')
    self._repr = f'{type(self).__name__}({self._str!r})'
    self._preds = tuple([VersionConstraintRelation(c) for c in re.split(r'\s*,\s*', self._str)])

  def __call__(self, other: CoerceableVersion) -> bool:
    version: Version = coerce_to_version(other)
    for pred in self._preds:
      if not pred.match(version):
        return False
    return True

  def __str__(self) -> str:
    return self._str

  def __repr__(self) -> str:
    return self._repr
