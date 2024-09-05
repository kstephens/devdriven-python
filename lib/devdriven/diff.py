from typing import Any, Dict, List, Optional
import platform
import os
from devdriven.util import exec_command
from devdriven.file import file_nlines

def diff_files(expected_file: str, actual_file: str, *diff_options: Any) -> Dict[str, Any]:
  if not (os.path.isfile(expected_file) and os.path.isfile(actual_file)):
    expected = file_nlines(expected_file)
    actual = file_nlines(actual_file)
    return {
      "correct": False,
      "expected": expected,
      "actual": actual,
      "old": None,
      "new": None,
      "differences": None,
      "correct_ratio": 0.0,
      "correct_percent": 0.0,
      "exit_code": 2,
    }
  return DIFF_FUNC(DIFF_PROG, expected_file, actual_file, *diff_options)

def diff_files_gnu(diff_cmd: str, expected_file: str, actual_file: str, *diff_options: Any) -> Dict[str, Any]:
  command = [
    diff_cmd,
    '--minimal',
    '--old-line-format=-\n',
    '--new-line-format=+\n',
    '--unchanged-line-format=',
    *diff_options,
    expected_file, actual_file]
  return diff_run(command, False, expected_file, actual_file)

def diff_files_bsd(diff_cmd: str, expected_file: str, actual_file: str, *diff_options: Any) -> Dict[str, Any]:
  command = [
    diff_cmd,
    '--minimal',
    '-U', '0',
    *diff_options,
    expected_file, actual_file]
  return diff_run(command, True, expected_file, actual_file)

def diff_run(command: List[str], has_fences: bool, expected_file: str, actual_file: str) -> Dict[str, Any]:
  expected = file_nlines(expected_file)
  actual = file_nlines(actual_file)
  diff_result = exec_command(command, check=False, capture_output=True)
  if diff_result.stderr:
    raise Exception(
      f"diff_files: failed : {diff_result.returncode}"
      f": {command!r} : "
      f"{diff_result.stderr.decode().splitlines()[:5]!r}"
    )
  old = new = 0
  lines = diff_result.stdout.splitlines()
  if has_fences:
    lines = [line for line in lines[2:] if not line.startswith(b'@@ ')]
  for line in lines:
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


if platform.system() == 'Darwin':
  if os.path.isfile('/opt/homebrew/bin/diff'):
    DIFF_PROG = '/opt/homebrew/bin/diff'
    DIFF_FLAVOR = 'gnu'
    DIFF_FUNC = diff_files_gnu
  else:
    DIFF_PROG = '/usr/bin/diff'
    DIFF_FLAVOR = 'bsd'
    DIFF_FUNC = diff_files_bsd
else:
  DIFF_PROG = 'diff'
  DIFF_FLAVOR = 'gnu'
  DIFF_FUNC = diff_files_gnu
