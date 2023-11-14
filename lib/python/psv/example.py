import re
import os
import sys
import subprocess
import shlex
import devdriven.cli.command as ddc
from devdriven.util import cwd, flat_map
from .command import Command, command

@command()
class Example(Command):
  '''
  examples - Show examples.

  Aliases: ex, example

  SEARCH-STRING | Matches name, aliases, brief

  --run, -r     | Run examples.
  '''
  def xform(self, _inp, _env):
    examples = list(flat_map(ddc.descriptors(), lambda cmd: cmd.examples))
    comment_rx = re.compile(f'(?i).*{"|".join(self.args)}.*')
    def match(x):
      return re.match(comment_rx, x)
    def command_matches(cmd):
      return match(cmd.command) or any(map(match, cmd.comments))
    examples = list(filter(command_matches, examples))
    self.run_examples(examples)

  def run_examples(self, examples):
    for ex in examples:
      for comment in ex.comments:
        print('# ' + comment)
      print('$ ' + ex.command)
      if self.opt('run', self.opt('r', False)):
        sys.stdout.flush()
        sys.stderr.flush()
        self.run_example(ex)
      print('')

  def run_example(self, ex):
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
    instance.run(cmd_argv)

  def run_command(self, cmd):
    # logging.warning('run_command: %s', repr(cmd))
    env = os.environ
    if env.get('PSV_RUNNING'):
      return
    env = env | {
      "PSV_RUNNING": '1',
      'PATH': f'{self.main.bin_dir}:{env["PATH"]}'
    }
    subprocess.run(cmd, shell=True, env=env)
