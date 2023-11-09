import re

class Command:
  def __init__(self):
    self.main = None
    self.argv = []
    self.name = None
    self.args = []
    self.opts = {}
    self.opts_defaults = {}
    self.opt_char_map = {}
    self.rtn = None

  def run(self, argv):
    self.parse_argv(argv)
    self.exec()

  def parse_argv(self, argv):
    self.argv = argv.copy()
    while argv:
      arg = argv.pop(0)
      if arg == '--':
        self.args.extend(argv)
        break
      if self.args:
        self.args.append(arg)
      elif mtch := re.match(r'^--([a-zA-Z][-_a-zA-Z0-9]*)=(.*)$', arg):
        self.opts[mtch.group(1)] = mtch.group(2)
      elif mtch := re.match(r'^--([a-zA-Z][-_a-zA-Z0-9]*)$', arg):
        self.opts[mtch.group(1)] = True
      elif mtch := re.match(r'^\+\+([a-zA-Z][-_a-zA-Z0-9]*)$', arg):
        self.opts[mtch.group(1)] = False
      elif mtch := re.match(r'^-([a-zA-Z][-_a-zA-Z0-9]*)$', arg):
        for flag in [*mtch.group(1)]:
          self.opts[self.opt_flag_name(flag)] = True
      elif mtch := re.match(r'^\+([a-zA-Z][-_a-zA-Z0-9]*)$', arg):
        for flag in [*mtch.group(1)]:
          self.opts[self.opt_flag_name(flag)] = False
      else:
        self.args.append(arg)
    return self

  def set_name(self, name):
    self.name = name
    return self

  def set_main(self, main):
    self.main = main
    return self

  def opt(self, key, *default):
    if key in self.opts:
      return self.opts[key]
    if default:
      return default[0]
    return self.opt_default(key)

  # OVERRIDE:
  def opt_default(self, key):
    return self.opts_defaults.get(key, None)

  def opt_flag_name(self, flag):
    return self.opt_char_map.get(flag, flag)

  # OVERRIDE:
  def exec(self):
    return self.rtn

