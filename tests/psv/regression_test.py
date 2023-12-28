import os
import re
import sys
from pathlib import Path

def test_example_regression():
  prog = str(Path('bin/psv').absolute())
  actual_out = f'{__file__}.out.actual'
  expect_out = f'{__file__}.out.expect'
  os.system(f'{prog} example -r > {actual_out}')
  with open(actual_out, 'r', encoding='utf-8') as io:
    actual_lines = io.readlines()
  if os.path.isfile(expect_out):
    with open(expect_out, 'r', encoding='utf-8') as io:
      expect_lines = io.readlines()
    log(f'Actual   : {actual_out} : {len(actual_lines)} lines')
    log(f'Expected : {expect_out} : {len(expect_lines)} lines')
    i = 0
    cmd = ''
    for actual_line, expect_line in zip(actual_lines, expect_lines):
      actual_line, expect_line = actual_line[:-1], expect_line[:-1]
      i += 1
      if re.match(r'^\$ ', actual_line):
        cmd = actual_line
        log(cmd)
      if re.match(r'^  "now": "\d\d\d\d-\d\d-\d\d', actual_line):
        continue
      if actual_line != expect_line:
        log(f'FAILED: Command: {cmd}')
        log(f'Actual   : {actual_line!r}')
        log(f'Expected : {expect_line!r}')
        assert (i, actual_line) == (i, expect_line)
  else:
    os.system(f'cp {actual_out} {expect_out}')

def log(msg):
  print(f'  ### {msg}', file=sys.stderr)
