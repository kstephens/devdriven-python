from typing import Any, Optional, Iterable, Callable, Tuple
import os
import sys
from pathlib import Path
import hashlib
from .file import file_md5

FilterFunc = Optional[Callable]

def assert_command_output(file: str,
                          command: str,
                          fix_line: FilterFunc = None,
                          context_line: FilterFunc = None):
  def run(actual_out):
    system_command = f'exec 2>&1; set -x; {command} > {actual_out!r}'
    os.system(system_command)
    assert_log(f'assert_command_output : {command!r}')
  return assert_output(file, run, fix_line, context_line)

def assert_output_by_key(
    key: str,
    directory: str,
    proc: Callable,
    fix_line: FilterFunc = None,
    context_line: FilterFunc = None):
  key_hash = hashlib.md5(key.encode('utf-8')).hexdigest()
  output_file = f'{directory}/{key_hash}'
  return assert_output(
    output_file,
    proc,
    fix_line=fix_line,
    context_line=context_line,
  )

def assert_output(file: str,
                  proc: Callable,
                  fix_line: FilterFunc = None,
                  context_line: FilterFunc = None):
  expect_out = f'{file}.out.expect'
  actual_out = f'{file}.out.actual'
  Path(expect_out).parent.mkdir(parents=True, exist_ok=True)
  result = proc(actual_out)
  assert_files(actual_out, expect_out,
               fix_line=fix_line, context_line=context_line)
  return result

def assert_files(actual_out: str,
                 expect_out: str,
                 fix_line: FilterFunc = None,
                 context_line: FilterFunc = None):
  if fix_line:
    fix_file(actual_out, fix_line)

  accept_actual = differences = None

  if os.path.isfile(expect_out):
    differences = compare_files(actual_out, expect_out, context_line=context_line)
    if differences:
      assert_log(f'To compare : diff -u {expect_out!r} {actual_out!r}')
      assert_log(f'To accept  : mv {actual_out!r} {expect_out!r}')
      assert_log('      OR   : export ASSERT_DIFF_ACCEPT=1')
      os.system(f'exec 2>&1; set -x; diff -u {expect_out!r} {actual_out!r} 2>&1')
      if int(os.environ.get('ASSERT_DIFF_ACCEPT', '0')):
        accept_actual = "ASSERT_DIFF_ACCEPT"
      else:
        assert actual_out == expect_out
  else:
    accept_actual = 'Initialize'

  if accept_actual:
    assert_log(f'{accept_actual} : {expect_out!r} from {actual_out!r}')
    os.system(f'exec 2>&1; mv {actual_out!r} {expect_out!r}')
  elif not differences:
    os.system(f'exec 2>&1; rm -f {actual_out!r}')

def compare_files(actual_out: str,
                  expect_out: str,
                  context_line: FilterFunc = None):
  with open(actual_out, 'r', encoding='utf-8') as io:
    actual_lines = io.readlines()
  with open(expect_out, 'r', encoding='utf-8') as io:
    expect_lines = io.readlines()

  actual_md5 = file_md5(actual_out)
  expect_md5 = file_md5(expect_out)

  if actual_md5 != expect_md5:
    assert_log(f'actual   : {actual_out!r} : {len(actual_lines)} lines : md5 {actual_md5!r}')
    assert_log(f'expected : {expect_out!r} : {len(expect_lines)} lines : md5 {expect_md5!r}')
  else:
    assert_log(f'SAME     : {actual_out!r} : {len(actual_lines)} lines : md5 {actual_md5!r}')
  return compare_lines(actual_lines, expect_lines, context_line=context_line)

def compare_lines(actual_lines: Iterable[str],
                  expect_lines: Iterable[str],
                  context_line: FilterFunc = None
                  ) -> Iterable[Tuple[int, str, str, Optional[str]]]:
  i = 0
  context = None
  differences = []
  for actual_line, expect_line in zip(actual_lines, expect_lines):
    actual_line, expect_line = actual_line[:-1], expect_line[:-1]
    i += 1
    if context_line:
      if new_context := context_line(actual_line):
        context = new_context
    if actual_line != expect_line:
      differences.append((i, actual_line, expect_line, context))
  return differences

def fix_file(file: str, fix_line: FilterFunc = None) -> None:
  # log(f'fix_file: {file!r}')
  file_tmp = f'{file}.tmp'
  with open(file_tmp, 'w', encoding='utf-8') as tmp:
    with open(file, 'r', encoding='utf-8') as out:
      while line := out.readline():
        if fix_line:
          line = fix_line(line)
        tmp.write(line)
  # os.system(f'diff -U0 {file} {file_tmp}')
  os.rename(file_tmp, file)

def assert_log(msg: Any = ''):
  if msg:
    print(f'  ### assert : {msg}', file=sys.stderr)
  else:
    print('', file=sys.stderr)
