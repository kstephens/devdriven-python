from typing import List, Dict
import logging
import shlex
import re

Command = List[str]

class MacroExpander:
  def __init__(self, macros: Dict[str, str], max_expansions: int = 16):
    self.macros = macros
    self.max_expansions = max_expansions

  def expand(self, command: Command) -> Command:
    prev = curr = command
    for _i in range(self.max_expansions):
      prev = curr
      curr = self.expand_macro(prev)
      if prev == curr:
        return curr
    logging.warning('config : command : expanded %d times %s ', self.max_expansions, command)
    return curr

  def expand_macro(self, command: Command) -> Command:
    name, *argv = command
    if macro := self.macros.get(name):
      def expand(m: re.Match) -> str:
        if m[1]:   # "$n"
          return shlex.join([get_safe(command, int(m[1]), '')])
        if m[2]:   # $n
          return get_safe(command, int(m[2]), '')
        if m[3] == '@':   # "$@"
          return shlex.join(argv)
        if m[3] == '*':   # "$*"
          return shlex.join([' '.join(argv)])
        if m[4]:  # $@ == $*
          return ' '.join(argv)
        assert not 'here'
        return '<<INVALID>>'
      exp = re.sub(MACRO_REFERERENCE_RX, expand, macro)
      return shlex.split(exp)
    return command


MACRO_REFERERENCE_RX = re.compile(r'(?:"\$(-?\d+)"|\$(-?\d+)|"\$([@*])"|\$([@*]))')

def get_safe(a: List[str], i: int, default: str) -> str:
  try:
    return a[i]
  except IndexError:
    return default
