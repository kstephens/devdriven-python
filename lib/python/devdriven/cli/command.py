import re

class Command:
  def __init__(self, main):
    self.main = main
    self.argv = []
    self.name = None
    self.args = []
    self.opts = {}
    self.rtn = None

  def parse_argv(self, argv):
    self.argv = argv.copy()
    while argv:
      arg = argv.pop(0)
      if arg == '--':
        self.args.extend(argv)
        break
      if self.args:
        self.args.append(arg)
      elif mtch := re.match(r'^--([a-zA-Z0-9][-_a-zA-Z0-9]*)=(.*)$', arg):
        self.opts[mtch.group(1)] = mtch.group(2)
      elif mtch := re.match(r'^--([a-zA-Z0-9][-_a-zA-Z0-9]*)$', arg):
        self.opts[mtch.group(1)] = argv.pop(0)
      elif mtch := re.match(r'^\+\+([a-zA-Z0-9][-_a-zA-Z0-9]*)$', arg):
        self.opts[mtch.group(1)] = False
      elif mtch := re.match(r'^-([a-zA-Z0-9][-_a-zA-Z0-9]*)$', arg):
        self.opts[mtch.group(1)] = True
      elif mtch := re.match(r'^\+([a-zA-Z0-9][-_a-zA-Z0-9]*)$', arg):
        self.opts[mtch.group(1)] = False
      else:
        self.args.append(arg)
    return self

  def set_name(self, name):
    self.name = name
    return self

  def run(self):
    return self.rtn

  def opt(self, key, *default):
    if key in self.opts:
      return self.opts[key]
    if default:
      return default[0]
    return self.opts_default()[key]

  def opts_default(self):
    return {
    }
