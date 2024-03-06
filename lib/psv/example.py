import re
import os
import subprocess
import shlex
from io import StringIO
# from icecream import ic
from devdriven.cli.application import app
from devdriven.util import cwd
import devdriven.html
from devdriven.combinator import re_pred
from devdriven.io import BroadcastIO
from devdriven.cache import PickleCache
from devdriven.resource import Resources
# from icecream import ic
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
    all_examples = PickleCache(
      path=resources.rel_path('example.pickle'),
      generate=self.generate_all)
    if self.opt('generate'):
      all_examples.set_data(self.generate_all())
    selected = self.find_examples(all_examples.data())
    output = BroadcastIO()
    output.push(StringIO())
    self.print_examples(selected, output)
    return output.pop().getvalue()

  def generate_all(self):
    all_examples = app.enumerate_examples()
    self.run_examples(all_examples)
    return all_examples

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

  def print_examples(self, examples: list, output: BroadcastIO):
    sec = cmd = None
    for sdc in examples:
      if sec != sdc.section.name:
        sec = sdc.section.name
        output.print(header(f' {sec}  ', '='))
      if cmd != sdc.descriptor.name:
        cmd = sdc.descriptor.name
        output.print(header(f'    {cmd}    ', '-'))
      self.print_example(sdc.example, output)

  def print_example(self, ex, output: BroadcastIO):
    for comment in ex.comments:
      output.print('# ' + comment)
    output.print('$ ' + ex.command)
    if self.opt('run'):
      output.write(ex.output)
    output.print('')

  def run_examples(self, examples: list) -> StringIO:
    os.environ['PSV_RAND_SEED'] = '12345678'
    output = BroadcastIO()
    output.push(StringIO())
    for sdc in examples:
      output.push(StringIO())
      self.run_example(sdc.example, output)
      sdc.output = output.pop().getvalue()
      # ic(sdc.output)
    return output.pop()

  def run_example(self, ex, output: BroadcastIO):
    output.push(StringIO())
    self.run_example_command(ex, output)
    ex.output = output.pop().getvalue()
    # ic(ex.output)

  def run_example_command(self, ex, output: BroadcastIO):
    with cwd(f'{self.main.root_dir}/example'):
      tokens = shlex.split(ex.command)
      shell_tokens = {'|', '>', '<', ';'}
      shell_meta = [token for token in tokens if token in shell_tokens]
      if re.match(r'^psv ', ex.command) and not shell_meta:
        self.run_main(ex, output)
      else:
        self.run_command(ex, output)

  def run_main(self, ex, output: BroadcastIO):
    cmd = ex.command
    # logging.warning('run_main: %s', repr(cmd))
    cmd_argv = shlex.split(cmd)
    instance = self.main.__class__()
    instance.stdout = instance.stderr = output
    instance.prog_path = self.main.prog_path
    result = instance.run(cmd_argv)
    if result.exit_code != 0:
      raise Exception(f'example run failed: {cmd}')
    return result

  def run_command(self, ex, output: BroadcastIO):
    cmd = ex.command
    # logging.warning('run_command: %s', repr(cmd))
    env = os.environ
    if env.get('PSV_RUNNING'):
      return
    env = env | {
      "PSV_RUNNING": '1',
      'PATH': f'{self.main.bin_dir}:{env["PATH"]}',
    }
    cmd = self.fix_command_line(cmd)
    result = subprocess.run(cmd, check=True, shell=True, env=env, capture_output=True)
    assert result.returncode == 0
    output.write(result.stdout.decode('utf-8'))
    output.write(result.stderr.decode('utf-8'))

  def fix_command_line(self, cmd):
    w3m_conf = devdriven.html.res_html.find(['w3m.conf'])
    assert w3m_conf
    cmd = re.sub(r'^(w3m -dump )', f'TERM=xterm-256color \\1 -config {w3m_conf} ', cmd, count=1)
    return cmd


def header(x: str, tick: str) -> str:
  return f'\n{x}\n{tick * len(x)}'
