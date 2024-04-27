from typing import Any, Optional, List, Dict, Callable
from dataclasses import dataclass, field
import os
import logging
import yaml
# from icecream import ic

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
    conf_val = self.conf and self.conf.get(key)
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

  def __getitem__(self, key: str) -> Any:
    return self.opt(key)


CONVERTERS = {}

def register_converter(key: str, converter: Converter):
  CONVERTERS[key] = converter

def identity(x: Any, _key: str):
  return x
