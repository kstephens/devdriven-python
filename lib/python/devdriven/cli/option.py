import re
from dataclasses import dataclass

@dataclass
class Option():
  kind: str = ''
  full: str = ''
  name: str = ''
  value: str = None
  description: str = ''
  default: str = None
  others: list = None

  def parse(self, arg, style='arg'):
    self.others = self.others or []
    if style == 'doc':
      if m := re.match(r'^(\S+?)  \|  (.*)', arg):
        arg, self.description = m[1], m[2]
      if m := re.match(r'Default: +(.+)\.? *$', self.description):
        self.default = m[1]
    def matched_long(kind, name, val):
      self.kind, self.full, self.name, self.value = \
        kind, f'--{name}', name, val
      return self
    def matched_flag(opt, kind, name, val):
      opt.kind, opt.full, opt.name, opt.value = \
        kind, f'-{name}', name, val
      return opt
    def matched_flags(kind, flags, val):
      flags = [*flags]
      matched_flag(self, kind, flags.pop(0), val)
      for flag in flags:
        self.others.append(matched_flag(Option(), kind, flag, val))
      return self
    if m := re.match(r'^--([a-zA-Z][-_a-zA-Z0-9]*)=(.*)$', arg):
      return matched_long('option', m[1], m[2])
    elif m := re.match(r'^--([a-zA-Z][-_a-zA-Z0-9]*)$', arg):
      return matched_long('flag', m[1], True)
    elif m := re.match(r'^\+\+([a-zA-Z][-_a-zA-Z0-9]*)$', arg):
      return matched_long('flag', m[1], False)
    elif m := re.match(r'^-([a-zA-Z][-_a-zA-Z0-9]*)$', arg):
      return matched_flags('flag', m[1], True)
    elif m := re.match(r'^\+([a-zA-Z][-_a-zA-Z0-9]*)$', arg):
      return matched_flags('flag', m[1], False)
    return None

