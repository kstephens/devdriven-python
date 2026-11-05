import json
import os
import sys
from functools import reduce
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from .replace_vars import replace_vars
from .util_2 import deep_merge, parse_args

Config = Dict[str, Any]

ROOT_DIR: Path = (Path(__file__).parent / "../..").absolute()


def read_revision() -> str:
    revision_file = ROOT_DIR / "REVISION"
    if not revision_file.is_file():
        return "unknown"
    return revision_file.read_text(encoding="utf-8").strip() or "unknown"


def config_file(config_yml, variables: Config) -> Config:
    with open(config_yml, "r", encoding="utf-8") as stream:
        content = replace_vars(stream.read(), variables)
        return yaml.load(content, Loader=yaml.FullLoader)


def merge(configs: List[dict]) -> Config:
    return dict(reduce(deep_merge, configs[1:], configs[0]))


def replace_variables(variables: Config, config: Config) -> Config:
    "Replace ${name} variables in strings."

    def walk(x: Any) -> Any:
        if isinstance(x, dict):
            return {walk(k): walk(v) for k, v in x.items()}
        if isinstance(x, list):
            return [walk(v) for v in x]
        if isinstance(x, str):
            return replace_vars(x, variables)
        return x

    return dict(walk(config))


def options_config(opts: dict) -> Tuple[Config, Config]:
    def fill(d, k):
        v = d[k] = d.get(k, {})
        return v

    options: dict = {}
    overrides: dict = {}
    for k, v in opts.items():
        if k.startswith("."):
            *path, end = k[1:].split(".")
            reduce(fill, path, overrides)[end] = v
        else:
            options[k] = v
    return options, overrides


def command_line(argv: List[str]) -> Config:
    args, opts = parse_args(argv, {})
    opts, overrides = options_config(opts)
    return {"argv": argv, "args": args, "opts": opts, "overrides": overrides}


def set_environ(environ, config) -> Config:
    for k, v in config.get("environ", {}).items():
        assert isinstance(k, str)
        if v is None:
            environ.pop(k, None)
        else:
            environ[k] = str(v)
    return config


envvar_prefix_default, env_default = "", "local"


def load_config(
    argv: List[str] | None = None,
    env: str | None = None,
    config_dir: str | None = None,
    env_prefix: str | None = None,
    environ=None,
) -> Config:
    "Return config for environment name"
    assert isinstance_or_none(argv, list)
    assert isinstance_or_none(env, str)
    assert isinstance_or_none(config_dir, str)
    assert isinstance_or_none(environ, dict)
    argv = argv or []
    if environ is None:
        environ = os.environ
    assert isinstance(environ, (dict, type(os.environ)))
    _, opts = parse_args(argv)
    env_prefix = env_prefix or envvar_prefix_default
    env = env or opts.get("env") or environ.get(f"{env_prefix}ENV") or env_default
    conf_dir = str(opts.get("config_dir") or config_dir or ROOT_DIR / "config")
    conf_dir = str(Path(os.path.normpath(conf_dir)).resolve())
    config_files = [
        os.path.normpath(f"{conf_dir}/{name}.yml") for name in ("default", env)
    ]
    cmd_line = command_line(argv)
    variables = dict(environ)
    overrides = cmd_line["overrides"]
    return set_environ(
        environ,
        merge(
            [
                merge([config_file(file, variables) for file in config_files]),
                overrides,
                {
                    "main": {
                        "env": env,
                        "argv": cmd_line,
                        "config_dir": config_dir,
                        "config_files": config_files,
                    }
                },
            ]
        ),
    )


def isinstance_or_none(x, cls):
    return x is None or isinstance(x, cls)

"""
def main(argv):
    opts = {"help": False, "output_format": "yaml"}
    _args, opts = parse_args(argv, opts)
    if opts["help"]:
        print(__doc__)
        return 0
    config = load_config(argv)
    output_format = opts["output_format"]
    if output_format == "yaml":
        yaml.dump(config, sys.stdout)
    elif output_format == "json":
        json.dump(config, sys.stdout, indent=2)
    else:
        raise AttributeError(f"invalid --output-format : {output_format!r}")
    return 0
"""
