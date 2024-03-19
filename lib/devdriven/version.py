from typing import Any, Union, Self, List
import re
import logging

class Version:
  _str: str
  _elems: List[Any]
  _repr: str

  def __init__(self, ver: Union[str, Self]):
    if isinstance(ver, Version):
      self._str = ver._str
      self._elems = ver._elems
      self._repr = ver._repr
      return
    self._str = ver
    self._elems = parse(ver)
    self._repr = f'<{type(self).__name__} {self._elems!r}>'

  def __str__(self) -> str:
    return self._str

  def __repr__(self) -> str:
    return self._repr

  def __eq__(self, other) -> bool:
    return self._str == typecheck(self, other, '==')._str

  def __ne__(self, other) -> bool:
    return self._str != typecheck(self, other, '!=')._str

  def __le__(self, other) -> bool:
    other = typecheck(self, other, '<=')
    return self._str == other._str or cmp(self, other, '<=') <= 0

  def __ge__(self, other) -> bool:
    other = typecheck(self, other, '>=')
    return self._str == other._str or cmp(self, other, '>=') >= 0

  def __lt__(self, other) -> bool:
    return cmp(self, other, '<') < 0

  def __gt__(self, other) -> bool:
    return cmp(self, other, '>') > 0


PARSE_RX = re.compile(r'(\d+)|([a-zA-Z]+)|([^\da-zA-Z]+)')

def parse(ver: str) -> List[Union[int, str]]:
  def decode(m):
    return int(m[1]) if m[1] else (m[2] or m[3])
  return [decode(m) for m in re.finditer(PARSE_RX, ver)]

def typecheck(self: Version, other: Union[Version, Any], name: str) -> Version:
  if isinstance(other, Version):
    return other
  if isinstance(other, str):
    logging.error('Coercing %s', other)
    return Version(other)
  raise TypeError(f'{name} not supported between instances of '
                  f'{type(self).__name__!r} and {type(other).__name__!r} : '
                  f'({self!r}) {name} {other!r}')

def cmp(ver1: Version, ver2: Any, name: str) -> int:
  # pylint: disable-next=protected-access
  return cmp_list(ver1._elems, typecheck(ver1, ver2, name)._elems)

def cmp_list(a: List[Any], b: List[Any]) -> int:
  for i in range(0, max(len(a), len(b))):
    if i >= len(a) or i >= len(b):
      break
    if (result := cmp_elem(a[i], b[i])) != 0:
      return result
  return cmp_elem(len(a), len(b))

def cmp_elem(a: Any, b: Any) -> int:
  # pylint: disable-next=unidiomatic-typecheck
  if type(a) != type(b):
    a, b = str(a), str(b)
  return cmp_same(a, b)

def cmp_same(a: Any, b: Any) -> int:
  if a > b:
    return 1
  if a < b:
    return -1
  return 0
