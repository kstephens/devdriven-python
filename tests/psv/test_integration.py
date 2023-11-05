import psv
import psv.main
from pathlib import Path
import shlex

def test_example():
  run('psv example')

def test_help():
  run('psv help')

def test_help_md():
  run('psv help md')

def test_help_markdown():
  run('psv help markdown')

def test_parse_subpipe():
  main = run('psv null a b {{ null c d }}')

def run(cmdline):
  args = shlex.split(cmdline)
  main = psv.main.Main()
  main.prog_path = str(Path('bin/psv').absolute())
  main.run(args)
  assert main.exit_code == 0
  return main

