from typing import Any, Union, List
import re
import logging
from icecream import ic

class Version:
  def __init__(self, ver: str):
    self._str = ver
    self._elems = parse_elements(ver)
    self._repr = f'<{type(self).__name__} {self._elems!r}>'

  def __str__(self) -> str:
    return self._str
  def __repr__(self) -> str:
    return self._repr

  def __eq__(self, other) -> bool:
    return self.cmp(other, '==') == 0
  def __ne__(self, other) -> bool:
    return self.cmp(other, '!=') != 0
  def __lt__(self, other) -> bool:
    return self.cmp(other, '<') < 0
  def __gt__(self, other) -> bool:
    return self.cmp(other, '>') >= 0
  def __le__(self, other) -> bool:
    return self.cmp(other, '<=') <= 0
  def __ge__(self, other) -> bool:
    return self.cmp(other, '>=') >= 0

  def cmp(self, other: Any, op: str) -> int:
    if isinstance(other, str):
      other = Version(other)
      logging.error('Coerced %s', repr(other))
    if isinstance(other, Version):
      return cmp_list(self._elems, other._elems)
    else:
      raise TypeError(f'{op} not supported between instances of {type(self).__name__!r} and {type(other).__name__!r} : ({self!r}) {op} {other!r}')

def parse_elements(ver: str) -> List[Union[int, str]]:
  ver = re.sub(r'([^\d\w]|_)', '\t', ver)
  ver = re.sub(r'([a-z]+)(\d+)', r'\1\t\2', ver)
  ver = re.sub(r'(\d+)([a-z]+)', r'\1\t\2', ver)
  # ver = re.sub(r'\t', r'\t', ver)
  elems = ver.split('\t')
  elems = [elem for elem in elems if elem]
  # elems = re.split('\t', ver)
  def decode(elem):
    if m := re.match(r'\d+', elem):
      return int(m[0])
    return elem
  return [decode(elem) for elem in elems]

def cmp_list(e1: List[Any], e2: List[Any]) -> int:
  for i in range(0, max(len(e1), len(e2))):
    if i >= len(e1) or i >= len(e2):
      break
    if (result := cmp(e1[i], e2[i])) != 0: return result
  return cmp_same(len(e1), len(e2))

def cmp(e1: Any, e2: Any) -> int:
  if type(e1) != type(e2):
    return cmp_same(e1, e2)
  return cmp_same(str(e1), str(e2))

def cmp_same(e1: Any, e2: Any) -> int:
  if e1 > e2:
    return 1
  if e1 < e2:
    return -1
  return 0
