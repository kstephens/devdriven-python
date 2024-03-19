from typing import Any, Union, List
import re
import logging
from icecream import ic

class Version:
  def __init__(self, ver: str):
    self._str = ver
    self._elems = parse(ver)
    self._repr = f'<{type(self).__name__} {self._elems!r}>'

  def __str__(self) -> str:
    return self._str
  def __repr__(self) -> str:
    return self._repr

  def __eq__(self, other) -> bool:
    return self._elems == typecheck(self, other, '==')
  def __ne__(self, other) -> bool:
    return self._elems != typecheck(self, other, '!=')
  def __lt__(self, other) -> bool:
    return cmp(self, other, '<') < 0
  def __gt__(self, other) -> bool:
    return cmp(self, other, '>') > 0
  def __le__(self, other) -> bool:
    return cmp(self, other, '<=') <= 0
  def __ge__(self, other) -> bool:
    return cmp(self, other, '>=') >= 0

PARSE_RX = re.compile(r'(\d+)|([a-zA-Z]+)|([^\da-zA-Z]+)')

def parse(ver: str) -> List[Union[int, str]]:
  def decode(m):
    return int(m[1]) if m[1] else (m[2] or m[3])
  return [decode(m) for m in re.finditer(PARSE_RX, ver)]

def typecheck(self: Version, other: Union[Version|Any], op: str) -> List[Union[int,str]]:
  if isinstance(other, Version):
    return other._elems
  if isinstance(other, str):
    logging.error('Coercing %s', other)
    return parse(other)
  raise TypeError(f'{op} not supported between instances of {type(self).__name__!r} and {type(other).__name__!r} : ({self!r}) {op} {other!r}')

def cmp(v1: Version, v2: Any, op: str) -> int:
  return cmp_list(v1._elems, typecheck(v1, v2, op))

def cmp_list(e1: List[Any], e2: List[Any]) -> int:
  for i in range(0, max(len(e1), len(e2))):
    if i >= len(e1) or i >= len(e2):
      break
    if (result := cmp_elem(e1[i], e2[i])) != 0: return result
  return cmp_same(len(e1), len(e2))

def cmp_elem(e1: Any, e2: Any) -> int:
  if type(e1) != type(e2):
    return cmp_same(e1, e2)
  return cmp_same(str(e1), str(e2))

def cmp_same(e1: Any, e2: Any) -> int:
  if e1 > e2:
    return 1
  if e1 < e2:
    return -1
  return 0
