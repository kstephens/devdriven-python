from typing import Any
import re
import os
import subprocess
import shlex
from pathlib import Path
from io import StringIO
from dataclasses import dataclass
from devdriven.cli.application import app
from devdriven.util import cwd
from devdriven.random import set_seed
import devdriven.html
from devdriven.combinator import re_pred
from devdriven.io import BroadcastIO
from devdriven.cache import PickleCache
from devdriven.resource import Resources
from .command import Command, section, command

section('Documentation', 200)

resources = Resources([]).add_file_dir(__file__, 'resources')

@command
class Example(Command):
  '''
  example - Show examples.

  Aliases: ex, examples

  SEARCH-STRING  |  Matches name, aliases, brief.
  --run, -r      |  Run examples.
  --generate     |  Generate and save examples.

  '''
  def xform(self, _inp, _env):
    registry = ExampleRegistry(main=self.main)
    all_examples = registry.all_examples(generate=self.opt('generate'))
    selected = self.find_examples(all_examples)
    runner, output = self.make_runner()
    runner.print_examples(selected)
    return output.pop().getvalue()

  # pylint: disable-next=too-many-locals
  def find_examples(self, all_sdc):
    # pred_any = re_pred(f'({"|".join(self.args)})')
    pred_ci = re_pred(f'(?i)-?({"|".join(self.args)})-?')
    pred_exact = re_pred(f'^-?({"|".join(self.args)})-?$')
    pred_prefix = re_pred(f'^-?({"|".join(self.args)})-?')
    arg0 = len(self.args) == 1 and self.args[0]

    def descriptor_matches(sdc, pred):
      return pred(sdc.descriptor.name) or any(filter(pred, sdc.descriptor.aliases))

    def descriptor_matches_exactly(sdc):
      return descriptor_matches(sdc, pred_exact)

    def descriptor_matches_prefix(sdc):
      return descriptor_matches(sdc, pred_prefix)

    def section_matches(sdc):
      return arg0 and pred_ci(sdc.section.name)

    def command_matches(sdc):
      return pred_ci(sdc.example.command) or any(map(pred_ci, sdc.example.comments[0:]))

    by_pre = list(filter(descriptor_matches_prefix, all_sdc))
    by_dsc = list(filter(descriptor_matches_exactly, all_sdc))
    by_sec = list(filter(section_matches, all_sdc))
    by_exa = list(filter(command_matches, all_sdc))
    # ic(len(by_pre))
    # ic(len(by_dsc))
    # ic(len(by_sec))
    # ic(len(by_exa))
    # example_sets = sorted([by_pre or by_dsc or by_sec or by_exa], key=len)
    result = by_pre or by_dsc or by_sec or by_exa or all_sdc
    # ic(list(map(lambda sdc: (sdc.descriptor.name, sdc.example.command), result)))
    return result

  def make_runner(self):
    output = BroadcastIO()
    output.push(StringIO())
    return (ExampleRunner(output=output,
                          main=self.main,
                          run=self.opt('run')),
            output)


@dataclass
class ExampleRegistry():
  main: Any

  def all_examples(self, generate=False):
    cache = PickleCache(
      path=resources.rel_path('example.pickle'),
      generate=self.generate_all)
    if generate:
      cache.set_data(self.generate_all())
    examples = cache.data()
    return examples

  def generate_all(self):
    all_examples = app.enumerate_examples()
    runner, _output = self.make_runner()
    runner.run_examples(all_examples)
    return all_examples

  def make_runner(self):
    output = BroadcastIO()
    output.push(StringIO())
    return (ExampleRunner(output=output,
                          main=self.main,
                          run=True),
            output)


@dataclass
class ExampleRunner:
  output: BroadcastIO
  main: Any
  run: bool

  def print_examples(self, examples: list):
    sec = cmd = None
    for sdc in examples:
      if sec != sdc.section.name:
        sec = sdc.section.name
        self.output.print(header(f' {sec}  ', '='))
      if cmd != sdc.descriptor.name:
        cmd = sdc.descriptor.name
        self.output.print(header(f'    {cmd}    ', '-'))
      self.print_example(sdc.example)

  def print_example(self, ex):
    for comment in ex.comments:
      self.output.print('# ' + comment)
    self.output.print('$ ' + ex.command)
    if self.run:
      self.output.write(ex.output)
    self.output.print('')

  def run_examples(self, examples: list) -> StringIO:
    self.output.push(StringIO())
    for sdc in examples:
      self.output.push(StringIO())
      self.run_example(sdc.example)
      sdc.output = self.output.pop().getvalue()
      # ic(sdc.output)
    return self.output.pop()

  def run_example(self, ex):
    self.output.push(StringIO())
    self.run_example_command(ex)
    ex.output = self.output.pop().getvalue()
    # ic(ex.output)

  def run_example_command(self, ex):
    tokens = shlex.split(ex.command)
    shell_tokens = {'|', '>', '<', ';'}
    shell_meta = [token for token in tokens if token in shell_tokens]
    if re.match(r'^psv ', ex.command) and not shell_meta:
      self.run_main(ex, self.main.root_dir, self.main.bin_dir)
    else:
      self.run_command(ex, self.main.root_dir, self.main.bin_dir)

  def run_main(self, ex, root_dir, bin_dir):
    def proc(*_args):
      cmd = ex.command
      # logging.warning('run_main: %s', repr(cmd))
      cmd_argv = shlex.split(cmd)
      instance = self.main.__class__()
      instance.stdout = instance.stderr = self.output
      instance.prog_path = self.main.prog_path
      result = instance.run(cmd_argv)
      if result.exit_code != 0:
        raise Exception(f'example run failed: {cmd}')
      return result
    self.run_in_context(ex, root_dir, bin_dir, proc)

  def run_command(self, ex, root_dir, bin_dir):
    def proc(ex, _root_dir, bin_dir):
      cmd = ex.command
      # logging.warning('run_command: %s', repr(cmd))
      env = os.environ
      if env.get('PSV_RUNNING'):
        return
      env = env | {
        "PSV_RUNNING": '1',
        'PATH': f'{bin_dir}:{env["PATH"]}',
        'LC_ALL': 'en_US.UTF-8',
        'LC_COLLATE': 'C',
      }
      cmd = self.fix_command_line(cmd)
      result = subprocess.run(cmd, check=True, shell=True, env=env, capture_output=True)
      self.output.write(result.stdout.decode('utf-8'))
      self.output.write(result.stderr.decode('utf-8'))
      assert result.returncode == 0
    self.run_in_context(ex, root_dir, bin_dir, proc)

  def run_in_context(self, ex, root_dir, bin_dir, proc):
    set_seed('12345678')
    os.environ['PSV_RAND_SEED'] = '12345678'
    root_dir = Path(root_dir).absolute()
    bin_dir = Path(bin_dir).absolute()
    with cwd(f'{root_dir}/example'):
      proc(ex, root_dir, bin_dir)

  def fix_command_line(self, cmd):
    w3m_conf = devdriven.html.res_html.find(['w3m.conf'])
    assert w3m_conf
    cmd = re.sub(r'^(w3m -dump )', f'TERM=xterm-256color \\1 -config {w3m_conf} ', cmd, count=1)
    return cmd


def header(x: str, tick: str) -> str:
  return f'\n{x}\n{tick * len(x)}'
