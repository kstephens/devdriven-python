import re
import os
import sys
import subprocess
import shlex
from devdriven.cli.application import app
from devdriven.util import cwd, flat_map
# from icecream import ic
from .command import Command, section, command

section('Documentation')

@command
class Example(Command):
  '''
  examples - Show examples.

  Aliases: ex, example

  SEARCH-STRING | Matches name, aliases, brief

  --run, -r     | Run examples.
  '''
  def xform(self, _inp, _env):
    # ???: move this to cli.application
    all_descriptors = app.descriptors
    all_examples = list(flat_map(all_descriptors, lambda cmd: cmd.examples))
    examples = None

    def desc_matches_exactly(desc):
      if len(self.args) != 1:
        return False
      return desc.name == self.args[0] or self.args[0] in desc.aliases

    match_rx = re.compile(f'(?i).*{"|".join(self.args)}.*')

    def match(x):
      return re.match(match_rx, x)

    def command_matches(cmd):
      return match(cmd.command) or any(map(match, cmd.comments[0:]))

    # Match descriptor exactly?
    descriptors = list(filter(desc_matches_exactly, all_descriptors))
    if len(descriptors) == 1:
      examples = list(flat_map(descriptors, lambda cmd: cmd.examples))
    else:
      examples = list(filter(command_matches, all_examples))
    if not examples:
      examples = all_examples
    self.run_examples(examples)

  def run_examples(self, examples):
    for ex in examples:
      self.run_example(ex)

  def run_example(self, ex):
    for comment in ex.comments:
      print('# ' + comment)
    print('$ ' + ex.command)
    if self.opt(('run', 'r'), False):
      sys.stdout.flush()
      sys.stderr.flush()
      self.run_example_command(ex)
    print('')
    sys.stdout.flush()
    sys.stderr.flush()

  def run_example_command(self, ex):
    with cwd(f'{self.main.root_dir}/example'):
      tokens = shlex.split(ex.command)
      shell_tokens = {'|', '>', '<', ';'}
      shell_meta = [token for token in tokens if token in shell_tokens]
      if re.match(r'^psv ', ex.command) and not shell_meta:
        self.run_main(ex.command)
      else:
        self.run_command(ex.command)

  def run_main(self, cmd):
    # logging.warning('run_main: %s', repr(cmd))
    cmd_argv = shlex.split(cmd)
    instance = self.main.__class__()
    instance.prog_path = self.main.prog_path
    result = instance.run(cmd_argv)
    if result.exit_code != 0:
      raise Exception("example run failed: {cmd}")
    return result

  def run_command(self, cmd):
    # logging.warning('run_command: %s', repr(cmd))
    env = os.environ
    if env.get('PSV_RUNNING'):
      return
    env = env | {
      "PSV_RUNNING": '1',
      'PATH': f'{self.main.bin_dir}:{env["PATH"]}'
    }
    subprocess.run(cmd, check=True, shell=True, env=env)
