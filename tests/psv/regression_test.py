import os
import re
import sys
from pathlib import Path

PROG = str(Path('bin/psv').absolute())

def test_help():
  assert_command_output('tests/psv/output/help', f'{PROG} help')

def test_example_r():
  def context_line(line):
    if re.match(r'^\$ ', line):
      log(line)
      return line
    return None

  def fix_line(line):
    if m := re.match(r'^( +"now": +")([^"]+)(")(.*)', line):
      line = m[1] + '...' + m[3] + m[4]  # re.sub(r'\d', 'X', m[2])
    return line

  assert_command_output('tests/psv/output/example-r',
                        f'{PROG} example -r',
                        fix_line=fix_line, context_line=context_line)

def assert_command_output(file, command, fix_line=None, context_line=None):
  expect_out = f'{file}.out.expect'
  actual_out = f'{file}.out.actual'
  Path(expect_out).parent.mkdir(parents=True, exist_ok=True)
  os.system(f'{command} > {actual_out}')
  log(f'Command  : {command!r}')
  assert_files(actual_out, expect_out,
               fix_line=fix_line, context_line=context_line)

def assert_files(actual_out, expect_out, fix_line=None, context_line=None):
  if fix_line:
    fix_file(actual_out, fix_line)
  if os.path.isfile(expect_out):
    compare_files(actual_out, expect_out, context_line=context_line)
  else:
    log(f'Initialize {expect_out!r} with {actual_out!r}')
    os.system(f'cp {actual_out} {expect_out}')

def compare_files(actual_out, expect_out, context_line=None):
  with open(actual_out, 'r', encoding='utf-8') as io:
    actual_lines = io.readlines()
  with open(expect_out, 'r', encoding='utf-8') as io:
    expect_lines = io.readlines()
  log(f'Actual   : {actual_out!r} : {len(actual_lines)} lines')
  log(f'Expected : {expect_out!r} : {len(expect_lines)} lines')
  compare_lines(actual_lines, expect_lines, context_line=context_line)

def compare_lines(actual_lines, expect_lines, context_line=None):
  i = 0
  context = None
  for actual_line, expect_line in zip(actual_lines, expect_lines):
    actual_line, expect_line = actual_line[:-1], expect_line[:-1]
    i += 1
    if context_line:
      if new_context := context_line(actual_line):
        context = new_context
    if actual_line != expect_line:
      log(f'FAILED   : Context: {context}')
      log(f'Actual   : {actual_line!r}')
      log(f'Expected : {expect_line!r}')
      assert (i, actual_line) == (i, expect_line)

def fix_file(file, fix_line):
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

def log(msg):
  print(f'  ### {msg}', file=sys.stderr)
