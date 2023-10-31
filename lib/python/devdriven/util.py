import os
import subprocess
import logging
import inspect
import time
from typing import Any, Iterable, List, Dict, Callable, Tuple, Union, Optional
from collections import defaultdict

Predicate = Callable[[Any], Any]
Func1 = Callable[[Any], Any]
FuncAny = Callable[..., Any]
SubprocessResult = Any  # subprocess.CompletedProcess

def maybe_decode_bytes(obj: Optional[bytes], encoding: str = 'utf-8') -> Optional[str]:
    if obj is None:
        return None
    try:
        return obj.decode(encoding)
    except UnicodeDecodeError:
        return None

def datetime_iso8601(obj: Any) -> Union[str, Any]:
    return obj.strftime('%Y-%m-%dT%H:%M:%S.%f%z')

def parse_commands(argv: List[str]) -> List[List[str]]:
    cmds = [ ]
    argvi = iter(argv)
    command = None
    while arg := next(argvi, None):
        if arg == ',':
            if command is not None:
                cmds.append(command)
            command = None
        else:
            if command is None:
                command = [ ]
            command.append(arg)
    if command:
        cmds.append(command)
    return cmds

def exec_command(cmd_line: List[str], **options: Any) -> SubprocessResult:
    msg = f'exec_command : {repr(cmd_line)} : ...'
    logging.info('%s', msg)
    (result, dt_ms) = elapsed_ms(subprocess.run, cmd_line, **options)
    logging.info(
        '%s',
        msg +
        f' : returncode {result.returncode} : ' +
        f'stdout {len_or_none(result.stdout)} bytes : ' +
        f'stderr {len_or_none(result.stderr)} bytes : ' +
        f'elapsed_ms {dt_ms:.3f}'
    )
    result.elapsed_ms = dt_ms
    return result

def exec_command_unless_dry_run(cmd_line: List[str], dry_run: bool, **options: Any) -> Optional[SubprocessResult]:
    if dry_run:
        logging.info('DRY-RUN : exec_command : %s', repr(cmd_line))
        return None
    return exec_command(cmd_line, **options)

def file_md5(file: str) -> Optional[str]:
    result = exec_command(['md5sum', file], check=False, capture_output=True)
    if result.returncode == 0:
        return str(result.stdout.decode('utf-8').split(' ')[0])
    return None

def len_or_none(obj: Any) -> Optional[int]:
    return len(obj) if obj else None

def none_as_blank(value: Any) -> Any:
    return '' if value is None else value

def read_file(name: str, default: Any = None) -> Union[bytes, Any]:
    try:
        with open(name, 'rb') as input_io:
            return input_io.read()
    except OSError:
        return default

def read_file_lines(name: str, default: Any = None) -> Union[List[str], Any]:
    try:
        return read_file(name).decode('utf-8').splitlines()
    # pylint: disable=broad-except
    except Exception:
        return default

def delete_file(path: str) -> bool:
    try:
        os.remove(path)
        return True
    except OSError:
        return False

def elapsed_ms(func: FuncAny, *args: Any, **kwargs: Any) -> Tuple[Any, float]:
    time_0 = time.time()
    result = func(*args, **kwargs)
    time_1 = time.time()
    return (result, (time_1 - time_0) * 1000)

def file_size(path: str, default: Any = None) -> Any:
    try:
        return os.stat(path).st_size
    except FileNotFoundError:  # might be a symlink to bad file.
        return default

def file_nlines(path: str, default: Any = None) -> Union[int, Any]:
    lines = read_file(path)
    if lines is None:
        return default
    if len(lines) == 0:
        return 0
    if lines[-1] != b'\n'[0]:
        lines += b'\n'
    return lines.count(b'\n')

def first(iterable: Iterable[Any], condition: Predicate = lambda x: True, default: Any = None) -> Any:
    for elem in iterable:
        if condition(elem):
            return elem
    return default

def flat_map(iterable: Iterable[Any], func: FuncAny, *args: Any, **kwargs: Any) -> Iterable[Any]:
    return [ elem for sublist in iterable for elem in func(sublist, *args, **kwargs) ]

def partition(seq: Iterable[Any], pred: Predicate) -> Tuple[List[Any], List[Any]]:
    true_elems: List[Any] = []
    false_elems: List[Any] = []
    for elem in seq:
        (true_elems if pred(elem) else false_elems).append(elem)
    return (true_elems, false_elems)

def frequency(seq: Iterable[Any]) -> Dict[Any, int]:
    counts: Dict[Any, int] = defaultdict(lambda: 0, {})
    for elem in seq:
        counts[elem] += 1
    return dict(counts.items())

def uniq_by(seq: Iterable[Any], key: Func1) -> Iterable[Any]:
    seen = set()
    result = []
    for elem in seq:
        val = key(elem)
        if val not in seen:
            seen.add(val)
            result.append(elem)
    return result

def not_implemented() -> None:
    raise NotImplementedError(inspect.stack()[1][3])

def diff_files(expected_file: str, actual_file: str, *diff_options: Any) -> Dict[str, Any]:
    expected = file_nlines(expected_file, None)
    actual = file_nlines(actual_file, None)
    command = [
        'diff',
        '--minimal',
        '--old-line-format=-%l\n',
        '--new-line-format=+%l\n',
        '--unchanged-line-format==%l\n',
        *diff_options,
        expected_file, actual_file]
    diff_result = exec_command(command, check=False, capture_output=True)
    old = new = 0
    for line in diff_result.stdout.splitlines():
        if line.startswith(b'-'):
            old += 1
        elif line.startswith(b'+'):
            new += 1
    return diff_files_stats(expected, actual, old, new, diff_result.returncode)

def diff_files_stats(expected: Optional[int], actual: Optional[int],
                     old: int, new: int, diff_exit_code: int) -> Dict[str, Any]:
    if expected is None or actual is None or diff_exit_code > 1:
        return {
            'correct': False,
            'expected': expected,
            'actual': actual,
            'old': None,
            'new': None,
            'differences': None,
            'correct_ratio': 0.0,
            'correct_percent': 0.0,
            'exit_code': diff_exit_code,
        }
    differences = old + new
    total = expected + actual
    correct = actual == expected and differences == 0 and diff_exit_code == 0
    correct_count = max(total - differences, 0)
    if correct and expected == actual:
        correct_ratio = 1.0
    else:
        correct_ratio = float(correct_count) / float(max(total, 1))
    correct_percent = round(correct_ratio * 100.0, 2)
    # Avoid rounding up to 100% when there are differences.
    if not correct and correct_percent >= 100.00:
        correct_ratio = 0.9999
        correct_percent = 99.99
    return {
        'correct': correct,
        'exit_code': diff_exit_code,
        'expected': expected,
        'actual': actual,
        'old': old,
        'new': new,
        'differences': differences,
        'correct_ratio': correct_ratio,
        'correct_percent': correct_percent,
    }
