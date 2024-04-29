from typing import Any, List, Dict
from dataclasses import dataclass, field
import logging
import shlex
import re
# from icecream import ic

Command = List[str]

@dataclass
class MacroExpander:
  macros: Dict[str, str]
  max_expansions: int = field(default=16)

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
      rx = r'(?:"\$(-?\d+)"|\$(-?\d+)|"\$([@*])"|\$([@*]))'
      def expand(m):
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
        return None
      exp = re.sub(rx, expand, macro)
      return shlex.split(exp)
    return command

def get_safe(a, i: int, default=None) -> Any:
  try:
    return a[i]
  except IndexError:
    return default
