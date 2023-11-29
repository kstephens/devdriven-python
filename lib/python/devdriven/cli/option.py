import re
from dataclasses import dataclass

@dataclass
class Option():
  style: str = ''
  kind: str = ''
  arg: str = ''
  full: str = ''
  name: str = ''
  value: str = None
  description: str = ''
  default: str = None
  aliases: list = None

  def parse_arg(self, arg):
    self.style = 'arg'
    self.aliases = []
    return self.parse_simple(arg)

  def parse_doc(self, arg):
    self.style = 'doc'
    self.aliases = []
    if m := re.match(r'^(.+)  Default: +(.+?)\.$', arg):
      self.default = m[2].strip()
    if m := re.match(r'^([^\|]+?)  \|  (.*)', arg):
      opts = re.split(r', ', m[1].strip())
      arg, self.description = opts.pop(0), m[2].strip()
      for opt in opts:
        self.aliases.append(self.parse_alias(opt, self))
    if result := self.parse_simple(arg):
      for other in self.aliases:
        other.kind = self.kind
    return result

  def parse_alias(self, opt, target):
    # ic(opt)
    alias = Option().parse_simple(opt)
    alias.style = target.style
    alias.kind = target.kind
    alias.aliases = []
    alias.description = target.description
    alias.default = target.default
    return alias

  def parse_simple(self, arg):
    def matched_long(kind, name, val):
      self.arg = arg
      self.kind, self.full, self.name, self.value = \
        kind, f'--{name}', name, val
      return self
    def matched_flag(opt, kind, name, val):
      self.arg = arg
      opt.kind, opt.full, opt.name, opt.value = \
        kind, f'-{name}', name, val
      return opt
    def matched_flags(kind, flags, val):
      flags = [*flags]
      matched_flag(self, kind, flags.pop(0), val)
      for flag in flags:
        self.aliases.append(matched_flag(Option(), kind, flag, val))
      return self
    if m := re.match(r'^--([a-zA-Z][-_a-zA-Z0-9]*)=(.*)$', arg):
      return matched_long('option', m[1], m[2])
    elif m := re.match(r'^--no-([a-zA-Z][-_a-zA-Z0-9]+)$', arg):
      return matched_long('flag', m[1], False)
    elif m := re.match(r'^--([a-zA-Z][-_a-zA-Z0-9]+)$', arg):
      return matched_long('flag', m[1], True)
    elif m := re.match(r'^\+\+([a-zA-Z][-_a-zA-Z0-9]+)$', arg):
      return matched_long('flag', m[1], False)
    elif m := re.match(r'^-([a-zA-Z][-_a-zA-Z0-9]*)$', arg):
      return matched_flags('flag', m[1], True)
    elif m := re.match(r'^\+([a-zA-Z][-_a-zA-Z0-9]*)$', arg):
      return matched_flags('flag', m[1], False)
    return None

  def synopsis(self):
    return ', '.join([self.full] + [opt.full for opt in self.aliases])

  def table_row(self):
    return [self.synopsis(), self.description]
