import shlex
from pathlib import Path
from io import StringIO
import psv
import psv.main

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

def test_help_raw():
  run('psv help --raw sort')

def test_parse_subpipe():
  run('psv i /dev/null // null a b {{ null c d }}', -1)

def run(cmdline, min_len=0):
  argv = shlex.split(cmdline)
  main = psv.main.Main()
  main.stdout = StringIO()
  main.stderr = StringIO()
  main.prog_path = str(Path('bin/psv').absolute())
  main.run(argv)
  assert main.exit_code == 0
  assert len(main.stdout.getvalue()) > min_len
  assert len(main.stderr.getvalue()) == 0
  return main
