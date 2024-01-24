import re
import os
import sys
import subprocess
import shlex
from devdriven.cli.application import app
from devdriven.util import cwd
from devdriven.html import resources
# from icecream import ic
from .command import Command, section, command

section('Documentation', 200)

@command
class Example(Command):
  '''
  examples - Show examples.

  Aliases: ex, example

  SEARCH-STRING  |  Matches name, aliases, brief.
  --run, -r      |  Run examples.

  '''
  def xform(self, _inp, _env):
    # ???: move this to cli.application
    match_ci_rx = re.compile(f'(?i).*{"|".join(self.args)}.*')
    match_rx = re.compile(f'.*{"|".join(self.args)}.*')

    def match_ci(x):
      return re.match(match_ci_rx, x)

    def match(x):
      return re.match(match_rx, x)

    def descriptor_matches_exactly(sdc):
      if len(self.args) != 1:
        return False
      return sdc.descriptor.name == self.args[0] or self.args[0] in sdc.descriptor.aliases

    def section_matches(sdc):
      if len(self.args) != 1:
        return False
      return match(sdc.section.name)

    def command_matches(sdc):
      return match_ci(sdc.example.command) or any(map(match_ci, sdc.example.comments[0:]))

    all = app.enumerate_examples()
    by_dsc = list(filter(descriptor_matches_exactly, all))
    by_sec = list(filter(section_matches, all))
    by_exa = list(filter(command_matches, all))
    examples = by_dsc or by_sec or by_exa or all

    self.run_examples(examples)

  def run_examples(self, examples: list):
    sec = cmd = None
    for sdc in examples:
      if sec != sdc.section.name:
        sec = sdc.section.name
        print('#========================================')
        print(f'#  {sec}')
        print('#=======================================\n')
      if cmd != sdc.descriptor.name:
        cmd = sdc.descriptor.name
        print('#----------------------------------------')
        print(f'#    {cmd}')
        print('#----------------------------------------\n')
      self.run_example(sdc.example)

  def run_example(self, ex):
    for comment in ex.comments:
      print('# ' + comment)
    print('$ ' + ex.command)
    if self.opt('run', False):
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
      raise Exception(f'example run failed: {cmd}')
    return result

  def run_command(self, cmd):
    # logging.warning('run_command: %s', repr(cmd))
    env = os.environ
    if env.get('PSV_RUNNING'):
      return
    env = env | {
      "PSV_RUNNING": '1',
      'PATH': f'{self.main.bin_dir}:{env["PATH"]}',
      # 'TERM': 'xterm-256color'
    }
    cmd = self.fix_command_line(cmd)
    subprocess.run(cmd, check=True, shell=True, env=env)

  def fix_command_line(self, cmd):
    w3m_conf = resources.find(['w3m.conf'])
    cmd = re.sub(r'^(w3m -dump )', f'TERM=xterm-256color \\1 -config {w3m_conf} ', cmd, count=1)
    return cmd
