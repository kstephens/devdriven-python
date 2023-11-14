import shlex
from pathlib import Path
import psv
import psv.main

def test_example():
  run('psv example')

def test_example_run():
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

def test_help_plain():
  run('psv help --raw sort')

def test_parse_subpipe():
  run('psv i /dev/null // null a b {{ null c d }}')

def run(cmdline):
  args = shlex.split(cmdline)
  main = psv.main.Main()
  main.prog_path = str(Path('bin/psv').absolute())
  main.run(args)
  assert main.exit_code == 0
  return main
