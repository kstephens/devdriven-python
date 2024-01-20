from typing import Any, Self, Optional, List, Dict
import re
import inspect
from dataclasses import dataclass, field
from devdriven.util import get_safe
from devdriven.cli.option import Option

@dataclass
class Options:
  argv: List[str] = field(default_factory=list)
  args: List[str] = field(default_factory=list)
  arg_by_name: Dict[str, str] = field(default_factory=dict)
  opts: List[Option] = field(default_factory=list)
  opt_by_name: Dict[str, Option] = field(default_factory=dict)
  opts_defaults: Dict[str, Any] = field(default_factory=dict)
  opt_char_map: Dict[str, str] = field(default_factory=dict)
  opt_aliases: Dict[str, Option] = field(default_factory=dict)
  delegate: Any = None

  def parse_argv(self, argv: List[str]) -> Self:
    self.argv = argv.copy()
    while argv:
      arg = argv.pop(0)
      if arg == '--':
        self.args.extend(argv)
        break
      if self.args:
        self.args.append(arg)
      elif opt := Option().parse_arg(arg):
        self.opts.append(opt)
        self.opt_by_name[opt.name] = opt
        self.set_opt(opt.name, opt.value)
        for alias in opt.aliases:
          self.opts.append(alias)
          self.opt_by_name[alias.name] = alias
          self.set_opt(alias.name, opt.value)
        opt.aliases = []
      else:
        self.args.append(arg)
    return self

  def set_opt(self, name: str, val: Any) -> None:
    key = self.opt_name_key(name)
    if key and self.opt_valid(key, val):
      self.opt_by_name[key].value = val
    else:
      raise Exception(f'Invalid option : {name!r}')

  def opt(self, key, *default) -> Any:
    if isinstance(key, tuple) and key:
      return self.opt(key[0], self.opt(key[1:], *default))
    assert isinstance(key, str)
    if opt := self.opt_by_name.get(key):
      return opt.value
    if default:
      return default[0]
    return self.opt_default(key)

  def arg_or_opt(self, i: int, k: str, default: Any) -> Any:
    return get_safe(self.args, i, get_safe(self.opt_by_name, k, default))

  def opt_valid(self, key: str, val: Any) -> Any:
    return self.maybe_delegate('opt_valid', True, key, val)

  def opt_default(self, key: str) -> Any:
    return self.maybe_delegate('opt_default', self.opts_defaults.get(key), key)

  def opt_name_key(self, flag: str) -> Optional[str]:
    return self.maybe_delegate('opt_name_key', self.opt_char_map.get(flag, flag), flag)

  def opt_name_normalize(self, name: str) -> Optional[str]:
    if opt := self.opt_by_name.get(name):
      return opt.name
    if alias := self.opt_aliases.get(name):
      return alias.alias_of

  # See: Descriptor
  def parse_docstring(self, line: str) -> Optional[Self]:
    m = None

    def add_arg(m):
      name = m[1].strip()
      self.arg_by_name[name] = m[2].strip()
      self.args.append(name)

    if m := re.match(r'^(-) *[\|] *(.*)', line):
      add_arg(m)
      return self
    if option := Option().parse_doc(line):
      self.opt_by_name[option.name] = option
      self.opts.append(option)
      for alias in option.aliases:
        self.opt_aliases[alias.name] = alias
      return self
    if m := re.match(r'^([^\|]+)[\|] *(.*)', line):
      add_arg(m)
      return self
    return None

  def command_synopsis(self) -> List[str]:
    cmd = []
    for opt in self.opts:
      opts = [opt.full]  # + [alias.full for alias in opt.aliases]
      cmd.append(f'[{", ".join(opts)}]')
    for arg in self.args:
      if arg.endswith(' ...') or len(self.args) > 1:
        arg = f'[{arg}]'
      cmd.append(arg)
    return cmd

  def get_opt(self, name: str, aliases=False) -> Optional[Option]:
    for opt in self.opts:
      if opt.name == name:
        return opt
      if aliases and name in opt.aliases:
        return opt
    return None

  def get_opt_aliases(self, opt) -> List[Any]:
    return [k for k, v in self.opt_aliases.items() if v == opt]

  def maybe_delegate(self, name: str, default: Any, *args) -> Any:
    if self.delegate and hasattr(self.delegate, name):
      attr = getattr(self, name)
      if inspect.ismethod(attr):
        return attr(*args)
    return default
