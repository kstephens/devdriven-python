import os
import re
import sys
from pathlib import Path

def test_example_regression():
  prog = str(Path('bin/psv').absolute())
  expect_out = f'{__file__}.out.expect'
  actual_out = f'{__file__}.out.actual'
  actual_tmp = f'{actual_out}.tmp'
  os.system(f'{prog} example -r > {actual_tmp}')
  with open(actual_out, 'w', encoding='utf-8') as io:
    with open(actual_tmp, 'r', encoding='utf-8') as tmp:
      while line := tmp.readline():
        io.write(fix_line(line))
  os.remove(actual_tmp)
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
      if actual_line != expect_line:
        log(f'FAILED: Command: {cmd}')
        log(f'Actual   : {actual_line!r}')
        log(f'Expected : {expect_line!r}')
        assert (i, actual_line) == (i, expect_line)
  else:
    os.system(f'cp {actual_out} {expect_out}')

def fix_line(line):
  if m := re.match(r'^( +"now": +")([^"]+)(")(.*)', line):
    line = m[1] + '...' + m[3] + m[4] # re.sub(r'\d', 'X', m[2])
  return line

def log(msg):
  print(f'  ### {msg}', file=sys.stderr)
