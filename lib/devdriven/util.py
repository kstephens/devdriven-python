from typing import Any, Union, Iterable, Callable, List, Mapping, Dict, Tuple
import os
import subprocess
import logging
import inspect
import time
import re
import sys
import traceback
import socket
import dataclasses
import math
import operator
from datetime import datetime, timezone
from contextlib import contextmanager
from collections import defaultdict
from icecream import ic

Indexable = Union[list, tuple, dict, Mapping]  # ???: is there a type for this?
Predicate = Callable[[Any], Any]
Func0 = Callable[[], Any]
Func1 = Callable[[Any], Any]
FuncAny = Callable[..., Any]
SubprocessResult = Any  # subprocess.CompletedProcess
Data = str | bytes
Number = int | float


ic.configureOutput(includeContext=True, contextAbsPath=True)


def identity(x: Any) -> Any:
    return x


#####################################################################
# Access


def get_safe(items: Indexable, key: Any, default=None) -> Any:
    try:
        return items[key]
    except (KeyError, IndexError):
        return default


def len_or_none(obj: Any) -> int | None:
    return len(obj) if obj else None


def none_as_blank(value: Any, blank: str = "") -> Any:
    return blank if value is None else value


#####################################################################
# String, Bytes


def shorten_string(a_str: str, max_len: int, placeholder: str = "...") -> str:
    assert max_len >= 0
    if len(a_str) > max_len:
        end = max(0, max_len - len(placeholder))
        return a_str[:end] + placeholder
    return a_str


def maybe_decode_bytes(obj: bytes | None, encoding: str = "utf-8") -> str | None:
    if obj is None:
        return None
    try:
        return obj.decode(encoding)
    except UnicodeDecodeError:
        return None


def unpad_lines(lines: List[str]) -> List[str]:
    lines = lines.copy()
    while lines and not lines[0]:
        lines.pop(0)
    if not lines:
        return lines
    if re.search(r"^\S", lines[0]):
        return lines
    pad = re.compile(r"^")
    for line in lines:
        if m := re.search(r"^( +)", line):
            pad = re.compile(f"^{m[1]}")
            break
    return [re.sub(pad, "", line) for line in lines]


def wrap_words(words: str, width: int, _punctuation: str = r"[.,?;:]") -> List[str]:
    result = []
    current = ""
    rx = re.compile(r"^(?P<left>.*?)(?P<sep>\s+|\n|[.,?;:])(?P<rest>.*)")
    while words:
        if m := re.match(rx, words):
            words = m["rest"]
            current += m["left"] + m["sep"]
        else:
            break
        if not 0 < len(current) <= width:
            result.append(current)
            current = ""
    if current:
        current += words
        result.append(current)
    return result


def splitkeep(s, delimiter):
    split = s.split(delimiter)
    datums = [substr + delimiter for substr in split[:-1]]
    if split[-1]:
        datums.append(split[-1])
    return datums


def humanize(
    num: float, precision: int = 2, radix: int = 1000, unit: str = ""
) -> Tuple[str, str]:
    if num == 0:
        return (str(num), unit)
    whole = int(math.log10(radix))
    fmt = f"%{whole}.{precision}f"
    if radix == 1024 and unit:
        unit = "i" + unit
    for denom in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if abs(num) < float(radix):
            return (fmt % num, denom + unit)
        num /= float(radix)
    return (fmt % num, "Y" + unit)


#####################################################################
# Time


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


# See: https://en.wikipedia.org/wiki/ISO_8601
DATETIME_ISO8601_FMT = "%Y-%m-%d %H:%M:%S.%f%z"
# DATETIME_ISO8601_FMT = '%Y%m%dT%H%M%S.%f%z'


def datetime_iso8601(val: datetime, zone: timezone | None = None) -> str:
    if not zone:
        zone = timezone.utc
    return val.replace(tzinfo=zone).strftime(DATETIME_ISO8601_FMT)


def convert_windows_timestamp_to_iso8601(ts_str: int | str) -> str:
    ts_milli = int(ts_str) / 1000
    return datetime_iso8601(datetime.fromtimestamp(ts_milli))


def datetime_diff_sec(a: datetime | None, b: datetime | None) -> float:
    if a is None or b is None:
        return 0
    return (a - b).total_seconds()


def datetime_diff_ms(a: datetime | None, b: datetime | None) -> float:
    if a is None or b is None:
        return 0
    return datetime_diff_sec(a, b) * 1000


def elapsed_ms(func: FuncAny, *args: Any, **kwargs: Any) -> Tuple[Any, float]:
    time_0 = time.time()
    result = func(*args, **kwargs)
    time_1 = time.time()
    return (result, (time_1 - time_0) * 1000)


def elapsed_ms_exception(
    exc_klass: Any, func: FuncAny, *args: Any, **kwargs: Any
) -> Tuple[Any, float, Exception | None]:
    time_0 = time.time()
    try:
        result = func(*args, **kwargs)
        time_1 = time.time()
        return (result, (time_1 - time_0) * 1000, None)
    # pylint: disable-next=broad-except
    except exc_klass as exc:
        time_1 = time.time()
        return (None, (time_1 - time_0) * 1000, exc)


#####################################################################
# Command


def parse_commands(argv: List[str], terminator: Any = None) -> List[List[str]]:
    cmds = []
    while argv:
        cmds.append(parse_command(argv, terminator))
    return cmds


def parse_command(argv: List[str], terminator: Any = None) -> List[str]:
    if not terminator:
        terminator = re.compile(r"^(.*),$")
    command = []
    while argv:
        arg = argv.pop(0)
        if m := re.match(terminator, arg):
            if m[1]:
                command.append(m[1])
            return command
        command.append(arg)
    return command


def exec_command(cmd_line: List[str], **options: Any) -> SubprocessResult:
    msg = f"exec_command : {repr(cmd_line)} : ..."
    logging.info("%s", msg)
    (result, dt_ms) = elapsed_ms(subprocess.run, cmd_line, **options)
    logging.info(
        "%s",
        "".join(
            [
                msg,
                f" : returncode {result.returncode} : ",
                f"stdout {len_or_none(result.stdout)} bytes : ",
                f"stderr {len_or_none(result.stderr)} bytes : ",
                f"elapsed_ms {dt_ms:.3f}",
            ]
        ),
    )
    result.elapsed_ms = dt_ms
    return result


def exec_command_unless_dry_run(
    cmd_line: List[str], dry_run: bool, **options: Any
) -> SubprocessResult | None:
    if dry_run:
        logging.info("DRY-RUN : exec_command : %s", repr(cmd_line))
        return None
    return exec_command(cmd_line, **options)


#####################################################################
# Dict


def merge_dicts(*dicts) -> dict:
    return {k: v for d in dicts for k, v in d.items()}


def merge_deep(a: Any, b: Any) -> Any:
    if isinstance(a, dict) and isinstance(b, dict):
        return a | {k: merge_deep(a.get(k), v) for k, v in b.items()}
    return b


def setattr_from_dict(obj, attrs: Dict[str, Any]) -> None:
    for name, val in attrs.items():
        setattr(obj, name, val)


def dataclass_from_dict(
    klass, opts: Dict, defaults: Dict[str, Any] | None = None
) -> Any:
    opts = (defaults or {}) | opts
    args = {f.name: opts[f.name] for f in dataclasses.fields(klass) if f in opts}
    return klass(**args)


def slice_keys(d: dict, ks: Iterable[Any]) -> Any:
    return {k: d[k] for k in ks if k in d}


def slice_indexs(lst: List[Any], keys: Iterable[int], default=None) -> List[Any]:
    r = range(-len(lst), len(lst))
    return [lst[i] if i in r else default for i in keys]


def slice_keys_compare(d1: dict, d2: dict) -> bool:
    return slice_keys(d1, d2.keys()) == d2


#####################################################################
# Sequence


def count(seq: Iterable[Any], pred: Callable[[Any], bool] | None = None) -> int:
    if pred:
        return sum(1 for x in seq if pred(x))
    return sum(1 for _ in seq)


def trim_list(lst: List[Any]) -> List[Any]:
    lst = lst.copy()
    while lst and not lst[0]:
        lst.pop(0)
    while lst and not lst[-1]:
        lst.pop(-1)
    return lst


def reorder_list(
    items: Iterable[Any], front: Iterable[Any], back: Iterable[Any]
) -> List:
    front = [i for i in front if i in items]
    back = [i for i in back if i in items]
    middle = items
    middle = [i for i in middle if i not in front]
    middle = [i for i in middle if i not in back]
    return front + middle + back


def first(condition: Predicate, iterable: Iterable[Any], default: Any = None) -> Any:
    for elem in iterable:
        if condition(elem):
            return elem
    return default


def flat_map(
    func: FuncAny, iterable: Iterable[Any], *args: Any, **kwargs: Any
) -> Iterable[Any]:
    return [elem for sublist in iterable for elem in func(sublist, *args, **kwargs)]


def split_flat(items, sep):
    return flat_map(lambda x: x.split(sep), items)


def partition(seq: Iterable[Any], pred: Predicate) -> Tuple[List[Any], List[Any]]:
    true_elems: List[Any] = []
    false_elems: List[Any] = []
    for elem in seq:
        (true_elems if pred(elem) else false_elems).append(elem)
    return (true_elems, false_elems)


def map_partition(xform: Callable, seq: Iterable[Any]) -> Mapping[Any, Any]:
    part: Mapping = defaultdict(list)
    for elem in seq:
        part[xform(elem)].append(elem)
    return part


def frequency(seq: Iterable[Any]) -> Dict[Any, int]:
    counts: Dict[Any, int] = defaultdict(lambda: 0, {})
    for elem in seq:
        counts[elem] += 1
    return dict(counts.items())


def chunks(items, width: int) -> Iterable[Iterable]:
    "Note: items is almost a Sized"
    width = max(1, width)
    return [items[i : i + width] for i in range(0, len(items), width)]


def uniq_by(seq: Iterable[Any], key: Func1) -> Iterable[Any]:
    result, seen = [], set()
    for elem in seq:
        val = key(elem)
        if val not in seen:
            seen.add(val)
            result.append(elem)
    return result


def min_max(
    itr: Iterable,
    compare: Callable[[Any, Any], bool] = operator.lt,
    key: Callable[[Any], Any] = identity,
) -> Tuple[Any, Any]:
    seen = False
    min_item = max_item = None
    min_val = max_val = None
    for item in itr:
        val = key(item)
        if seen:
            if compare(val, min_val):
                min_val, min_item = val, item
            elif compare(max_val, val):
                max_val, max_item = val, item
        else:
            seen = True
            min_val = max_val = val
            min_item = max_item = item
    return min_item, max_item


#####################################################################
# Range


def parse_range(x: str, n: int) -> None | range:
    if m := re.match(r"^(-?\d+)?:(-?\d+)?(?::(-?\d+))?$", x):
        if m[0] == "-" or m[1] == "-" or m[2] == "-":
            return None
        return make_range(int(m[1] or 0), int(m[2] or n), int(m[3] or 1), n)
    return None


def make_range(start: Number, end: Number, step: Number, n: Number) -> range | None:
    if not start:
        start = 0
    if not end:
        end = n
    if not step:
        step = 1
    if step == 0:
        return None
    if start < 0:
        start = n + start
    if end < 0:
        end = n + end
    if step > 0 and start > end:
        step = -step
    return range(start, end, step)  # type: ignore[arg-type]


#####################################################################
# Current Directory


@contextmanager
def cwd(path: str) -> Any:
    oldpwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)


#####################################################################
# Regexp


def glob_to_rx(glob: str, glob_terminator: str | None = None) -> re.Pattern:
    assert not glob_terminator
    rx = glob
    rx = rx.replace(".", r"[^/]")
    rx = rx.replace("*", r"[^/]*")
    rx = rx.replace("?", r"[^/][^/]?")
    return re.compile(r"^" + rx + r"$")


def set_from_match(obj, match: re.Match):
    setattr_from_dict(obj, match.groupdict())


#####################################################################
# Networking


def ip_to_host(ip: str) -> str | None:
    try:
        return socket.gethostbyaddr(ip)[0].lower()
    # pylint: disable-next=bare-except
    # pylint: disable-next=broad-exception-caught
    except Exception:
        return None


def host_short(host):
    return host and re.sub(r"\..+$", "", host).lower()


#####################################################################
# Misc


def memoize(f: Callable[[Any], Any]) -> Callable[[Any], Any]:
    memo: Dict[Any, Any] = {}

    def g(x):
        if x in memo:
            return memo[x]
        result = memo[x] = f(x)
        return result

    return g


def not_implemented() -> None:
    raise NotImplementedError(inspect.stack()[1][3])


def printe(x):
    print(x, file=sys.stderr)


def module_fullname(obj) -> str:
    """
    Does not work as expected.
    """
    klass = obj.__class__
    module = klass.__module__
    if module == "builtins":
        return klass.__qualname__  # avoid outputs like 'builtins.str'
    return module + "." + klass.__qualname__


class RawRepr:
    def __init__(self, x: Any) -> None:
        self._x: Any = x

    def __repr__(self) -> str:
        return str(self._x)

    def __str__(self) -> Any:
        return self._x


# pylint: disable-next=invalid-name
def rr(x: Any) -> RawRepr:
    """Returns an object where `__repr__` it `str(x)`."""
    return RawRepr(x)


#####################################################################
# Logging


def configure_logging(app_name, log_level="INFO"):
    # We'd prefer JSON, but the solution is way too complicated:
    # See https://stackoverflow.com/questions/50144628/python-logging-into-file-as-a-dictionary-or-json
    # format = '%(asctime)s %(name)s %(levelname)s %(message)s'
    # https://code.activestate.com/lists/python-list/727185:
    # %(className)s func=%(funcName)s
    fmt = f"%(asctime)s %(levelname)-6s {app_name} %(message)s"
    # formatter = logging.Formatter(fmt)
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format=fmt)
    set_logging_level(log_level)


def set_logging_level(log_level):
    # https://stackoverflow.com/a/55490202
    # https://stackoverflow.com/a/2557316
    # https://stackoverflow.com/a/60381742
    numeric_level = getattr(logging, str(log_level).upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level!r}")
    loggers = [logging.getLogger()]  # get the root logger
    loggers += root_loggers()
    for logger in loggers:
        logger.setLevel(numeric_level)


def root_loggers() -> Iterable[Any]:
    # Is this dependent on Python version?
    # E1101: Instance of 'RootLogger' has no 'loggerDict' member (no-member)
    try:
        # pylint: disable-next=no-member
        return [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    # pylint: disable-next=bare-except
    # pylint: disable-next=broad-exception-caught
    except Exception:
        pass
    return []


def log_exc(exc, exc_info, prefix=None, suffix=None):
    msg = " : ".join(
        [str(s) for s in [prefix, "EXCEPTION", repr(exc), suffix] if s is not None]
    )
    logging.error(msg)
    for line in traceback.format_exception(*exc_info):
        logging.error("%s", f"{msg} : backtrace : {line.rstrip()}")
    return msg


def progress_logger(output=None) -> Callable[[int], None]:
    if not output:
        output = sys.stderr
    denom = 1
    i_prev = None

    def log(i: int) -> None:
        nonlocal denom, i_prev, output
        if i is None:
            output.write(f"{i_prev}.\n")
            output.flush()
            i = i_prev
        else:
            i_prev = i
        if i // denom == 10:
            denom *= 10
        if not i % denom:
            output.write(f"{i},")
            output.flush()

    return log
