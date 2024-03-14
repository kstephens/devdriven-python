import sys
import re
import shlex
from io import StringIO
from pathlib import Path
from devdriven.io import BroadcastIO
from devdriven.asserts import assert_output_by_key
from devdriven.cli.application import app
import psv.main
from psv.example import ExampleRunner

####################################

def test_example_generate():
  run('psv example --generate')

def test_example():
  run('psv example')

def test_example_run():
  run('psv example -r')

def test_example_run_range():
  run('psv example --run range')

def test_help():
  run('psv help')

def test_help_md():
  run('psv help md')

def test_help_markdown():
  run('psv help markdown')

def test_help_verbose():
  run('psv help --verbose sort')

def test_help_plain():
  run('psv help --plain sort')

def test_help_section():
  run('psv help --sections')

def test_help_list():
  run('psv help --list')

def test_help_raw():
  run('psv help --raw sort')

def test_parse_subpipe():
  run('psv i /dev/null // null a b {{ null c d }}', -1)

####################################

def test_all_examples():
  for cpr in app.enumerate_examples():
    assert_example(cpr)

def assert_example(cpr):
  def run_with_file(actual_out):
    with open(actual_out, "w", encoding='utf-8') as capture_output:
      key_hash = re.sub(r'\..+$', '', Path(actual_out).name)
      output = BroadcastIO([sys.stderr, capture_output])
      output = BroadcastIO([capture_output])
      output.print(f'# {key_hash}')
      output.print(f'$ {cpr.example.command}')
      runner = ExampleRunner(main=None, output=output, run=True)
      runner.run_command(cpr.example, '.', 'bin')

  assert_output_by_key(
    cpr.example.command,
    'tests/psv/output/example',
    run_with_file,
    fix_line=fix_line
  )

def run(cmdline, min_len=0):
  def run_with_file(actual_out):
    with open(actual_out, "w", encoding='utf-8') as capture_output:
      argv = shlex.split(cmdline)
      main = psv.main.Main()
      main.prog_path = str(Path('bin/psv').absolute())
      main.stdout = StringIO()
      main.stderr = StringIO()
      main.run(argv)
      capture_output.write(main.stdout.getvalue())
      capture_output.write(main.stderr.getvalue())
      assert main.exit_code == 0
      assert len(main.stdout.getvalue()) > min_len
      assert len(main.stderr.getvalue()) == 0
      return main

  assert_output_by_key(
    cmdline,
    'tests/psv/output/example',
    run_with_file,
    fix_line=fix_line
  )

def fix_line(line):
  if m := re.match(r'^( +"now": +")([^"]+)(")(.*)', line):
    line = m[1] + '...' + m[3] + m[4]  # re.sub(r'\d', 'X', m[2])
  return line
