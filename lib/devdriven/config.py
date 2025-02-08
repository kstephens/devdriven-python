from typing import Any, Self, List, Dict, Callable
from dataclasses import dataclass, field
import os
import logging
import yaml  # type: ignore

Command = List[str]
Converter = Callable[[Any], Any]


@dataclass
class Config:
    file: str | None = field(default=None)
    file_default: str | None = field(default=None)
    opts: Dict[str, str] = field(default_factory=dict)
    conf: Dict[str, str] = field(default_factory=dict)
    env_prefix: str = field(default_factory=str)
    env: Dict[str, str] = field(default_factory=dict)
    converters: Dict[str, Converter] = field(default_factory=dict)
    file_loaded: str | None = field(default=None)
    parent: Any | None = field(default=None)

    def __post_init__(self):
        self.cache = {}

    def config_file(self) -> str | None:
        return self.get_opt_env("config_file") or self.file or self.file_default

    def load_file(self, file: str, ok_if_missing: bool = True):
        file = os.path.expanduser(file)
        if ok_if_missing and not os.path.exists(file):
            return
        with open(file, encoding="utf-8") as inp:
            logging.info("config : load_file : %s : loading", file)
            self.conf = yaml.full_load(inp)
            self.file_loaded = file
            self.flush_cache()

    def load(self, ok_if_missing: bool = True) -> Self:
        if file := self.config_file():
            self.load_file(file, ok_if_missing=ok_if_missing)
        return self

    def flush_cache(self) -> None:
        self.cache = {}

    def opt(
        self,
        key: str,
        default: Any | None = None,
        converter: Converter | None = None,
    ) -> Any:
        if not self.cache:
            self.cache = {}
        if key in self.cache:
            return self.cache[key]
        val = self.cache[key] = self.get_opt(key, default, converter)
        return val

    def get_opt(
        self,
        key: str,
        default: Any | None = None,
        converter: Converter | None = None,
    ) -> Any:
        val: Any = None
        opts_val = self.opts.get(key)
        env_val = self.get_opt_env(key)
        conf_val = self.conf and self.conf.get(key)
        if env_val is not None:
            val = env_val
        elif opts_val is not None:
            val = opts_val
        elif conf_val is not None:
            val = conf_val
        elif self.parent:
            val = self.parent.get_opt(key, default, converter)
        else:
            val = default
        val = self.convert(key, val, converter)
        return val

    def get_opt_env(self, key: str) -> Any:
        env_key = (self.env_prefix + key).upper().replace("-", "_")
        return self.env.get(env_key)

    def convert(self, key: str, value: Any, converter: Converter | None) -> Any:
        if converter := converter or self.converters.get(key):
            return converter(value)
        return value

    def __getitem__(self, key: str) -> Any:
        return self.opt(key)
