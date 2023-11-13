import re
import pandas as pd
from tabulate import tabulate
from .formats import MarkdownOut
from .command import Command, command, descriptors, DEFAULTS

@command()
class Help(Command):
  '''
  help - This help document.

  --verbose, -v   : Show more detail.
  '''
  def xform(self, _inp, env):
    commands = all_commands = descriptors()
    if self.args:
      commands = filter(lambda cmd: self.command_matches(cmd, self.argv[0]), all_commands)
    return self.do_commands(commands, env)
  def do_commands(self, commands, env):
    tab = pd.DataFrame(columns=['command', 'description'])
    def row(*cols):
      tab.loc[len(tab.index)] = cols
    def emit_opts(title, opts):
      if opts:
        row('', '')
        row('', title)
        table = list(opts.items())
        for line in tabulate(table, tablefmt="presto").splitlines():
          row('', line)

    for desc in commands:
      row(desc.name, desc.synopsis)
      if desc.aliases:
        row('', 'Aliases: ' + ', '.join(desc.aliases))
      if self.opt('verbose', self.opt('v')):
        row('', '')
        for text in desc.detail:
          row('', text)
        emit_opts('Arguments:', desc.args)
        emit_opts('Options:', desc.opts)
        row('', '')
    return MarkdownOut().xform(tab, env)
  def command_matches(self, desc, pattern):
    desc = '|'.join([desc.name, desc.synopsis] + desc.aliases)
    return re.match(re.compile(f'(?i).*{pattern}.*'), desc)

@command()
class HelpVerbose(Help):
  '''
  help-verbose - This help document.
  Alias: help+
  '''
  def do_commands(self, commands, _env):
    lines = []
    def row(*cols):
      lines.append(''.join(['  '] + list(cols[1:])))
    def emit_opts(title, opts):
      if opts:
        row('', '')
        row('', title)
        row('', '')
        table = list(opts.items())
        for line in tabulate(table, tablefmt="presto").splitlines():
          line = line[1:]
          row('', line)

    attrs = list(DEFAULTS.keys())
    for desc in commands:
      # row('', "'''")
      row('', desc.name, ' - ', desc.synopsis)
      if desc.aliases:
        row('', '')
        row('', 'Aliases: ' + ', '.join(desc.aliases))
      for text in desc.detail:
        row('', text)
      emit_opts('Arguments:', desc.args)
      emit_opts('Options:', desc.opts)
      if desc.examples:
        row('', '')
        for attr in attrs:
          val = getattr(desc, attr)
          if val:
            row(f':{attr}={val}')
      if desc.examples:
        row('', '')
        row('', 'Examples:')
        row('', '')
        for example in desc.examples:
          row('', example)
      # row('', "'''")
      row('', '')
      row('', '                    ==========================================================')
      row('', '')
    return '\n'.join(lines + [''])
