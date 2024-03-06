from typing import Any, Dict, Optional
from devdriven.util import exec_command
from devdriven.file import file_nlines

def diff_files(expected_file: str, actual_file: str, *diff_options: Any) -> Dict[str, Any]:
  expected = file_nlines(expected_file)
  actual = file_nlines(actual_file)
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
