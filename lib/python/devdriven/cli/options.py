import re
from devdriven.util import get_safe, set_from_match, dataclass_from_dict, dataclass_from_dict, unpad_lines
from devdriven.cli.option import Option
# from icecream import ic

# ??? use @dataclass?
class Options:
  def __init__(self):
    self.argv = []
    self.args = []
    self.arg_by_name = {}
    self.opts = []
    self.opt_by_name = {}
    self.opts_defaults = {}
    self.opt_char_map = {}
    self.opt_aliases = {}

  def parse_argv(self, argv):
    self.argv = argv.copy()
    while argv:
      arg = argv.pop(0)
      if arg == '--':
        self.args.extend(argv)
        break
      if self.args:
        self.args.append(arg)
      elif opt := Option().parse_arg(arg):
        self.opt_by_name[opt.name] = opt
        self.set_opt(opt.name, opt.value)
        for alias in opt.aliases:
          self.opt_by_name[alias.name] = opt
          self.set_opt(alias.name, opt.value)
      else:
        self.args.append(arg)
    return self

  def set_opt(self, name, val):
    key = self.opt_name_key(name)
    if self.opt_valid(key, val):
      self.opts[key] = val
    else:
      raise Exception(f'Invalid option : {name!r}')

  def opt(self, key, *default):
    if isinstance(key, tuple) and key:
      return self.opt(key[0], self.opt(key[1:], *default))
    if key in self.opts:
      return self.opts[key]
    if default:
      return default[0]
    return self.opt_default(key)

  def arg_or_opt(self, i, k, default):
    return get_safe(self.args, i, get_safe(self.opts, k, default))

  # OVERRIDE: via delegate?
  def opt_valid(self, _key, _val):
    return True

  # OVERRIDE: via delegate?
  def opt_default(self, key):
    return self.opts_defaults.get(key, None)

  # OVERRIDE: via delegate?
  def opt_name_key(self, flag):
    return self.opt_char_map.get(flag, flag)

  # See: Descriptor
  def parse_docstring(self, line):
    m = None
    def add_arg(m):
      name = m[1].strip()
      self.arg_by_name[name] = m[2].strip()
      self.args.append(name)
    if m := re.match(r'^(-) *[\|] *(.*)', line):
      add_arg(m)
      return self
    elif option := Option().parse_doc(line):
      self.opt_by_name[option.name] = option
      self.opts.append(option)
      return self
    elif m := re.match(r'^([^\|]+)[\|] *(.*)', line):
      add_arg(m)
      return self
    return None

  def command_synopsis(self):
    cmd = []
    for opt in self.opts:
      opts = [opt.full]  # + [alias.full for alias in opt.aliases]
      cmd.append(f'[{", ".join(opts)}]')
    for arg in self.args:
      if arg.endswith(' ...') or len(self.args) > 1:
        arg = f'[{arg}]'
      cmd.append(arg)
    return cmd

  def get_opt(self, name, aliases=False):
    for opt in self.opts:
      if opt.name == name:
        return opt
      if aliases and name in opt.aliases:
        return opt
    return None

  def get_opt_aliases(self, opt):
    return [k for k, v in self.opt_aliases.items() if v == opt]
