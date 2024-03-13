import sys
import hashlib
import re
from psv.example import ExampleRunner
from devdriven.io import BroadcastIO
from devdriven.asserts import assert_output
from devdriven.cli.application import app

def test_all_examples():
  for cpr in app.enumerate_examples():
    assert_example(cpr)

def assert_example(cpr):
  cmd = cpr.example.command
  md5 = hashlib.md5(cmd.encode('utf-8')).hexdigest()
  def run(actual_out):
    with open(actual_out, "w", encoding='utf-8') as capture_output:
      output = BroadcastIO([sys.stderr, capture_output])
      output = BroadcastIO([capture_output])
      output.print(f'# {md5}')
      output.print(f'$ {cpr.example.command}')
      runner = ExampleRunner(main=None, output=output, run=True)
      runner.run_command(cpr.example, '.', 'bin')

  assert_output(f'tests/psv/output/example/{md5}', run,
                fix_line=fix_line)

def fix_line(line):
  if m := re.match(r'^( +"now": +")([^"]+)(")(.*)', line):
    line = m[1] + '...' + m[3] + m[4]  # re.sub(r'\d', 'X', m[2])
  return line
