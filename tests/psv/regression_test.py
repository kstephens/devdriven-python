import re
from pathlib import Path
from devdriven.asserts import assert_command_output, log
from devdriven.cli.application import app

PROG = str(Path('bin/psv').absolute())

def test_help():
  assert_command_output('tests/psv/output/help', f'{PROG} help')

def test_help_plain():
  assert_command_output('tests/psv/output/help-plain', f'{PROG} help --plain')

def test_example_r():
  command = f'{PROG} example -r'

  def context_line(line):
    if re.match(r'^\$ ', line):
      log(f'command : {line}')
      return line
    return None

  def fix_line(line):
    if m := re.match(r'^( +"now": +")([^"]+)(")(.*)', line):
      line = m[1] + '...' + m[3] + m[4]  # re.sub(r'\d', 'X', m[2])
    return line

  assert_command_output('tests/psv/output/example-r',
                        command,
                        fix_line=fix_line, context_line=context_line)

