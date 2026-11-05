import json
import logging
import math
import os
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Tuple

import yaml
from pythonjsonlogger.json import JsonFormatter

lib_dir: Path = Path(".").absolute()
lib_dir_prefix: str = f"{lib_dir}/"


Args = List[str]
Opts = Dict[str, Any]

# These should not be rescued in almost all circumstances:
PROTECTED_EXCEPTIONS = (
    SystemExit,
    KeyboardInterrupt,
    InterruptedError,
    GeneratorExit,
    StopIteration,
    # AssertionError,  # ???
)


def blank_or(x, y):
    return y if x is None or x == "" else x


def one_or_none(x):
    x = list(x)
    return x[0] if x and len(x) == 1 else None


def frequency(values: Iterable) -> Dict[Any, int]:
    result: Dict[Any, int] = {}
    for v in values:
        result[v] = result.get(v, 0) + 1
    return result


def fill(values: list, width: int, value: Any = None):
    if (padding := width - len(values)) > 0:
        values.extend([value] * padding)


def subdict(d: dict, ks: Iterable) -> dict:
    return {k: v for k, v in d.items() if k in ks}


def subdict_strict(d: dict, ks: Iterable) -> dict:
    return {k: d[k] for k in ks}


def subdict_equal(d1: dict, d2: dict) -> bool:
    "Returns true if the intersection of keys from both dicts are equal."
    common_keys = set(d1.keys()) & set(d2.keys())
    return subdict(d1, common_keys) == subdict(d2, common_keys)


def get_values(
    d: dict, keys: Iterable, default: Any = None, defaults: dict | None = None
) -> Iterable:
    def get_default(k):
        if defaults and k in defaults:
            return defaults[k]
        return default

    return [d.get(k, get_default(k)) for k in keys]


def rename_keys(d: dict, key_mapping: dict) -> dict:
    "Renames each key_mapping (to, from) in d and returns d."
    for new, old in key_mapping.items():
        if old in d:
            d[new] = d.pop(old)
    return d


def copy_keys(d: dict, key_mapping: dict, defaults=None) -> dict:
    "Copy each key_mapping {to: from} in d and returns d."
    defaults = defaults or {}
    for new, old in key_mapping.items():
        d[new] = d[old] if old in d else defaults.get(new)
    return d


def remove_keys(d: dict, keys) -> dict:
    "Removes all k in keys.  Returns d."
    for k in keys:
        d.pop(k, None)
    return d


def remove_values(d: dict, val) -> dict:
    "Removes (k, v) where v == val.  Returns d."
    for k, v in list(d.items()):
        if v == val:
            d.pop(k)
    return d


def isnan_safe(x: Any) -> bool:
    return isinstance(x, float) and math.isnan(x)


def replace_nan(x: Any, value: Any = None) -> Any:
    def walk(x: Any) -> Any:
        if isnan_safe(x):
            return value
        if isinstance(x, tuple):
            return tuple(walk(v) for v in x)
        if isinstance(x, list):
            return [walk(v) for v in x]
        if isinstance(x, dict):
            return {k: walk(v) for k, v in x.items()}
        return x

    return walk(x)


def dir_dict(obj) -> dict:
    vals = [(k, getattr(obj, k)) for k in dir(obj)]
    return {
        k: v
        for k, v in vals
        if isinstance(v, (int, str, float, list, dict)) and not k.startswith("__")
    }


def dict_without_none(d):
    "Return a new dict without None values."
    return {k: v for k, v in d.items() if v is not None}


def split_dict(d: dict, ks: Iterable) -> Tuple[dict, dict]:
    "Move keys in ks to the second dict."
    return partition_dict(lambda k, v: k not in ks, d)


def partition_dict(pred: Callable[[Any, Any], bool], d: dict) -> Tuple[dict, dict]:
    "a contains all (k, v) where pred(k, v)."
    a: dict = {}
    b: dict = {}
    for k, v in d.items():
        (a if pred(k, v) else b)[k] = v
    return a, b


def partition(pred: Callable[[Any], bool], seq: Iterable) -> Tuple[list, list]:
    "a contains all x where pred(x)."
    a: list = []
    b: list = []
    for x in seq:
        (a if pred(x) else b).append(x)
    return a, b


def deep_merge(a: Any, b: Any) -> Any:
    if isinstance(a, dict) and isinstance(b, dict):
        a = a.copy()
        for k, v in b.items():
            a[k] = deep_merge(a.get(k), v)
        return a
    return b


def mapcat(f: Callable[[Any], Any], seq: Iterable) -> Iterable:
    for x in seq:
        yield from map(f, x)


def compose(*fs: Callable) -> Callable:
    """
    Composes Callables, such that:
    compose(f, g, h)(2, 3, a=5) == f(g(h(2, 3, a=5))).
    """
    name = "compose(" + ",".join(f.__name__ for f in fs) + ")"  # type: ignore
    *fs, f = fs  # type: ignore
    if not fs:
        return f  # type: ignore

    def h(*args, **kwargs):
        x = f(*args, **kwargs)
        for g in fs:
            x = g(x)
        return x

    h.__name__ = h.__qualname__ = name
    return h


def combine_names(
    g: Callable, name: str, f: Callable, with_module: bool = False
) -> Callable:
    """
    Set g's __qualname__ as "name(f)".
    Useful to give function combinations readable names.
    """
    if with_module:
        g.__qualname__ = f"{name}({f.__module__}.{f.__qualname__})"
    else:
        g.__qualname__ = f"{name}({f.__qualname__})"
    return g


def none_or(f: Callable[[Any], Any]) -> Callable[[Any], Any | None]:
    """
    Returns a Callable g(x) that will return None if x is None,
    Otherwise, returns f(x).
    """

    def g(x, *args, **kwargs) -> Any | None:
        if x is None:
            return None
        return f(x, *args, **kwargs)

    return g


def indexed(i) -> Callable[[Any], Any]:
    """Returns a function that returns a lookup against the first arguments."""
    return lambda x: x[i]


def parse_args(argv: Iterable[str], opts: Opts | None = None) -> Tuple[Args, Opts]:
    "Dead simple --flag and --option=value parser."
    argv, args, opts = list(argv).copy(), [], dict(opts or {}).copy()
    while argv:
        arg = argv.pop(0)
        if arg == "--":
            args.extend(argv)
            break
        if m := re.search(r"(?i)^--([a-z.][-_a-z.]*)=(.*)$", arg):
            opts[m[1].replace("-", "_")] = m[2]
        elif m := re.search(r"(?i)^--([a-z.][-_a-z.]*)$", arg):
            opts[m[1].replace("-", "_")] = True
        elif m := re.search(r"(?i)^\+\+([a-z.][-_a-z.]*)$", arg):
            opts[m[1].replace("-", "_")] = False
        elif m := re.search(r"(?i)^-([a-z.][-_a-z.]*)$", arg):
            for f in m[1]:
                opts[f] = True
        elif m := re.search(r"(?i)^\+([a-z.][-_a-z.]*)$", arg):
            for f in m[1]:
                opts[f] = False
        else:
            args.append(arg)
    return args, opts


def redact(s: str, redact_str: str = "*", min_size: int = 8) -> str:
    n = len(s)
    if n == 0:
        i, j = 0, 0
    elif n == 1:
        i, j = 1, n
    else:
        i, j = 1, -1
    m = max(0, n - 2, min_size)
    return s[0:i] + redact_str * m + s[j:n]


def count_lines(file: str, buf_size=64 * 1024) -> int:
    count = 0
    with open(file, encoding="utf-8") as io:
        while buf := io.read(buf_size):
            count += buf.count("\n")
    return count


def output_response(response: Any, fmt: str, stream=sys.stdout):
    if fmt == "none":
        return response
    if fmt == "json":
        json.dump(response, fp=stream, indent=2)
        print("", file=stream)
    elif fmt == "yaml":
        yaml.dump(response, stream=stream)
    else:
        print(repr(response), file=stream)
    return response


def read_file_str(file: str | Path) -> str:
    return Path(file).read_text(encoding="utf-8")


def write_file_str(file: str | Path, data: str):
    return Path(file).write_text(data, encoding="utf-8")


#############################################


def setup_logging(**kwargs):
    config = logging_config(kwargs)
    formatter = config.pop("formatter", os.environ.get("LOG_FORMAT"))
    LOGGING_CONFIG.update(config | {"formatter": formatter})
    config.pop("format_prefix", None)
    drop_fields = config.pop("drop_fields", [])
    logging.basicConfig(**config)
    if formatter:
        if formatter == "json":

            def json_serializer(x, **kwargs):
                for k in drop_fields:
                    x.pop(k, None)
                return json.dumps(x, **kwargs)

            formatter = JsonFormatter(
                "{created}{asctime}{process}{name}{levelname}{message}",
                style="{",
                datefmt=config["datefmt"],
                json_serializer=(json_serializer if drop_fields else json.dumps),
            )
        set_logger_formatter(logging.getLogger(), formatter)
        for log in all_loggers():
            set_logger_formatter(log, formatter)
    LOGGING_CONFIG.update({"formatter": formatter})
    return LOGGING_CONFIG


def logging_config(kwargs):
    prefix = kwargs.get("format_prefix", "-")
    level = kwargs.get("level") or os.environ.get("LOG_LEVEL") or "INFO"
    if isinstance(level, str):
        level = logging.getLevelNamesMapping()[level.upper()]
    return (
        {
            "stream": sys.stderr,
            "level": level,
            "format": f"%(asctime)s %(levelname)-8s %(process)d {prefix} %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S.%s%z",
        }
        | LOGGING_CONFIG
        | kwargs
    )


def set_logger_formatter(logger, formatter):
    for handler in logger.handlers:
        handler.setFormatter(formatter)


def all_loggers():
    # E1101: Instance of 'RootLogger' has no 'loggerDict' member (no-member)
    # pylint: disable-next=no-member
    return [logging.getLogger(name) for name in logging.root.manager.loggerDict]


LOGGING_CONFIG: dict = {}

#############################################

LoggingCallback = Callable[[logging.LogRecord], None]


class LoggingCallbackHandler(logging.Handler):
    def __init__(self, callback: LoggingCallback, level: int = logging.INFO):
        super().__init__()
        self.callback = callback
        self.level = level
        self.filters = []
        self.lock = None

    def emit(self, record):  # pragma: no cover
        try:
            self.callback(record)
        except PROTECTED_EXCEPTIONS as exc:
            raise exc
        # pylint: disable-next=bare-except
        except:
            self.handleError(record)


def with_log_collection(callback: LoggingCallback, proc: Callable) -> Any:
    logger = logging.getLogger()
    handler = LoggingCallbackHandler(callback)
    try:
        logger.addHandler(handler)
        return proc()
    finally:
        logger.removeHandler(handler)


#############################################


def execute(
    func, *args, capture_exception=True, tz: timezone | None = None, log=True
) -> dict:
    "Runs func(*args) capturing elapsed time, result or exception."
    tz = tz or timezone.utc
    t0 = t1 = datetime.now(tz)

    if log:
        logging.info(f"{func.__qualname__} : started")

    result, exc, error = {}, None, None
    try:
        result = func(*args)
    except PROTECTED_EXCEPTIONS as e:
        raise e
    # pylint: disable-next=broad-exception-caught
    except Exception as e:
        if capture_exception:
            exc = e
        else:
            raise e

    t1 = datetime.now(tz)
    elapsed_sec = (t1 - t0).total_seconds()
    elapsed_ms = round(elapsed_sec * 1000.0, 2)

    error = error_data(
        result_error if (result_error := result.get("error")) is not None else exc
    )
    if log:
        logging.info(f"{func.__qualname__} : finished : {elapsed_ms} ms")
    if error:
        logging.error(
            f"{func.__qualname__} : error : {error['class']} : {error['message']}"
        )

    return {
        "result": result,
        "error": error,
        "started_at": t0.isoformat(),
        "finished_at": t1.isoformat(),
        "elapsed_ms": elapsed_ms,
        "pid": os.getpid(),
    }


def error_data(error: Any) -> Dict[str, Any] | None:
    if error is None:
        return None
    if isinstance(error, dict):
        return error
    if isinstance(error, Exception):
        return {
            "class": type(error).__qualname__,
            "message": str(error),
            "backtrace": [f"{file}:{line}" for file, line in backtrace_list(error)],
        }
    return {
        "class": type(error).__qualname__,
        "message": str(error),
        "backtrace": [],
    }


def merge_error(dst, src):
    errors = dst["errors"] = dst.get("errors", [])
    if error := src["error"]:
        errors.append(error)
        dst["error"] = error
    return src


Backtrace = List[Tuple[str, int]]


def backtrace_list(exc: BaseException) -> Backtrace:
    trb = exc.__traceback__
    trb_extracted = traceback.extract_tb(trb)
    return [
        (
            clean_filename(frame.filename),
            frame.lineno or 0,
        )
        for frame in trb_extracted
    ]


def clean_filename(f: Path | str) -> str:
    return str(Path(f).absolute()).removeprefix(lib_dir_prefix)
