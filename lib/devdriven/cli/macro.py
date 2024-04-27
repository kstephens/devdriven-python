from typing import Any, List, Dict
from dataclasses import dataclass, field
import logging
import shlex
import re
from icecream import ic

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
      prev = curr
    logging.warning('config : command : expanded %d times %s ', self.max_expansions, command)
    return curr

  def expand_macro(self, command: Command) -> Command:
    name, *argv = command
    # ic(name); ic(argv)

    if expansion := self.macros.get(name):
      ic(expansion)
      exp = ''
      exp_i = 0
      for m in re.finditer(r'(?:"\$(-?\d+)"|\$(-?\d+)|"\$(@)"|\$(@))', expansion):
        exp += expansion[exp_i:m.span()[0]]
        exp_i = m.span()[1]
        if i := m[1] or m[2]:
          val = get_safe(command, int(i), '')
          if m[1]:   # quoted
            exp += shlex.join([val])
          else:
            exp += str(val)
        elif m[3]:   # quoted
          exp += shlex.join(argv)
        elif m[4]:
          exp += ' '.join(argv)
      exp += expansion[exp_i:]
      return shlex.split(exp)
    return command

def get_safe(a, i: int, default=None) -> Any:
  try:
    return a[i]
  except IndexError:
    return default
