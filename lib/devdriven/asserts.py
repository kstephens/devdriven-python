from typing import Any, Optional, Iterable, Callable, Tuple, TextIO
import os
import sys
from pathlib import Path
import hashlib
from pprint import pprint
from .file import file_md5

FilterFunc = Callable[[str], str]
Filepath = str
Command = str
FileOutputFunc = Callable[[Filepath], None]
ContextFunc = Callable[[str], Optional[str]]
Difference = Tuple[int, str, str, Optional[str]]
Differences = Iterable[Difference]

def assert_command_output(file: Filepath,
                          command: Command,
                          fix_line: Optional[FilterFunc] = None,
                          context_line: Optional[ContextFunc] = None) -> Filepath:
  def run(actual_out: Filepath) -> None:
    system_command = f'exec 2>&1; set -x; {command} > {actual_out!r}'
    os.system(system_command)
    assert_log(f'assert_command_output : {command!r}')
  return assert_output(file, run, fix_line, context_line)

def assert_output_by_key(
    key: str,
    directory: Filepath,
    proc: FileOutputFunc,
    fix_line: Optional[FilterFunc] = None,
    context_line: Optional[ContextFunc] = None) -> Filepath:
  key_hash = hashlib.md5(key.encode('utf-8')).hexdigest()
  output_file = f'{directory}/{key_hash}'
  return assert_output(
    output_file,
    proc,
    fix_line=fix_line,
    context_line=context_line,
  )

def assert_output(file: Filepath,
                  proc: FileOutputFunc,
                  fix_line: Optional[FilterFunc] = None,
                  context_line: Optional[ContextFunc] = None) -> Filepath:
  expect_out = f'{file}.out.expect'
  actual_out = f'{file}.out.actual'
  Path(expect_out).parent.mkdir(parents=True, exist_ok=True)
  proc(actual_out)
  return assert_files(actual_out, expect_out,
                      fix_line=fix_line, context_line=context_line)

def assert_files(actual_out: Filepath,
                 expect_out: Filepath,
                 fix_line: Optional[FilterFunc] = None,
                 context_line: Optional[ContextFunc] = None) -> str:
  if fix_line:
    fix_file(actual_out, fix_line)

  accept_actual = differences = None

  if os.path.isfile(expect_out):
    differences = compare_files(
      actual_out, expect_out,
      context_line=context_line
    )
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
    Path(actual_out).replace(expect_out)
    return expect_out
  if not differences:
    Path(actual_out).unlink(missing_ok=True)
    return expect_out
  return actual_out

def compare_files(actual_out: Filepath,
                  expect_out: Filepath,
                  context_line: Optional[ContextFunc] = None) -> Differences:
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
  return compare_lines(
    actual_lines, expect_lines,
    context_line=context_line
  )

def compare_lines(actual_lines: Iterable[str],
                  expect_lines: Iterable[str],
                  context_line: Optional[ContextFunc] = None
                  ) -> Differences:
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

def fix_file(file: Filepath, fix_line: Optional[FilterFunc] = None) -> None:
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

def assert_log(msg: Optional[str] = '') -> None:
  if msg:
    print(f'  ### assert : {msg}', file=sys.stderr)
  else:
    print('', file=sys.stderr)

######################################


Outputter = Callable[[TextIO], None]

def open_output(proc: Outputter) -> FileOutputFunc:
  def f(file: Filepath) -> None:
    with open(file, "w", encoding='utf-8') as output:
      proc(output)
  return f

def pp_output(data: Any) -> Outputter:
  def f(output: TextIO) -> None:
    pprint(data, stream=output, indent=2)
  return f

def lines_output(data: Any) -> Outputter:
  def make_line(row: Any) -> str:
    if isinstance(row, Iterable):
      return ' '.join([str(x) for x in row])
    return str(row)

  def f(output: TextIO) -> None:
    for row in data:
      print(make_line(row), file=output)
  return f
