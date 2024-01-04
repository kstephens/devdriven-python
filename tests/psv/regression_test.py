import re
from pathlib import Path
from devdriven.asserts import assert_command_output, log

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
