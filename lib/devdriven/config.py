from typing import Any, Optional, List, Dict, Callable
from dataclasses import dataclass, field
import os
import logging
import yaml
import shlex
import re
from icecream import ic

Command = List[str]
Converter = Callable[[Any, str], Any]

@dataclass
class Config:
  file: Optional[str] = field(default=None)
  file_default: Optional[str] = field(default=None)
  opts: Dict[str, str] = field(default_factory=dict)
  conf: Dict[str, str] = field(default_factory=dict)
  env_prefix: str = field(default_factory=str)
  env: Dict[str, str] = field(default_factory=dict)
  converters: Dict[str, Converter] = field(default_factory=dict)
  file_loaded: Optional[str] = field(default=None)
  cache: Dict[str, Any] = field(default_factory=dict)
  parent: Optional[Any] = field(default=None)

  def config_file(self):
    return self.file or self.opt('config_file') or self.file_default

  def load_file(self, file: str):
    file = os.path.expanduser(file)
    logging.info("config : load_file : %s", file)
    if os.path.exists(file):
      with open(file, encoding='utf-8') as inp:
        logging.info("config : load_file : %s : loading", file)
        self.conf = yaml.full_load(inp)
        self.file_loaded = file

  def load(self):
    if file := self.config_file():
      self.load_file(file)
    # ic(self)
    return self

  def opt(self, key: str, default: Optional[Any] = None, converter: Optional[Converter] = None) -> Any:
    if key in self.cache:
      return self.cache[key]
    self.cache[key] = val = self.get_opt(key, default, converter)
    return val

  def get_opt(self, key: str, default: Optional[Any] = None, converter: Optional[Converter] = None) -> Any:
    val = None
    opts_val = self.opts.get(key)
    env_key = (self.env_prefix + key).upper().replace('-', '_')
    env_val = self.env.get(env_key)
    conf_val = self.conf.get(key)
    if opts_val is not None:
      val = opts_val
    elif env_val is not None:
      val = env_val
    elif conf_val is not None:
      val = conf_val
    elif self.parent:
      val = self.parent.get_opt(key, default, converter)
    else:
      val = default
    val = self.convert(key, val, converter)
    return val

  def convert(self, key: str, value: Any, converter: Optional[Converter]):
    converter = converter or self.converters.get(key) or CONVERTERS.get(key) or identity
    return converter(value, key)

  def __getitem__(self, key: str, default: Optional[Any]) -> Any:
    return self.opt(key, default)

CONVERTERS = {}

def register_converter(key: str, converter: Converter):
  CONVERTERS[key] = converter

def identity(x: Any, _key: str):
  return x


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
    logging.warning('config : command : expanded %d times %s ', max_expansions, command)
    return curr

  def expand_macro(self, command: Command) -> Command:
    name, *argv = command
    ic(name); ic(argv)

    if expansion := self.macros.get(name):
      ic(expansion)
      exp = ''
      exp_i = 0
      for m in re.finditer(r'(?:"\$(-?\d+)"|\$(-?\d+)|"\$(@)"|\$(@))', expansion):
        exp += expansion[exp_i : m.span()[0]]
        exp_i = m.span()[1]
        if i := m[1] or m[2]:
          v = get_safe(command, int(i), '')
          if m[1]:   # quoted
            exp += shlex.join([v])
          else:
            exp += str(v)
        elif a := m[3] or m[4]:
          if m[3]:   # quoted
            exp += shlex.join(argv)
          else:
            exp += ' '.join(argv)
      exp += expansion[exp_i:]
      return shlex.split(exp)
    return command

def get_safe(a, i, default=None):
  try:
    return a[i]
  except IndexError:
    return None

