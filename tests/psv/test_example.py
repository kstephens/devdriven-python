import psv.main
from pathlib import Path

def test_example():
  instance = psv.main.Main()
  instance.prog_path = str(Path('bin/psv').absolute())
  instance.run(['psv', 'example'])
  assert instance.exit_code == 0
