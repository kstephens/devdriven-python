import re
import pandas as pd
from tabulate import tabulate
from devdriven.to_dict import to_dict
from devdriven.cli.descriptor import DEFAULTS
from devdriven.cli.command import descriptors
from .command import Command, begin_section, descriptors_by_sections, command
from .formats import MarkdownOut, JsonOut
from icecream import ic

begin_section('Documentation')

@command
class Help(Command):
  '''
  help - This help document.

  --verbose, -v   |  Show more detail.
  --plain, -p     |  Show plain docs.
  --raw, -r       |  Raw detail.
  '''
  def xform(self, _inp, env):
    commands = all_commands = descriptors_by_sections()
    if self.args:
      pattern = '|'.join([f'\\b{arg}\\b' for arg in self.args])
      rx = re.compile(f'(?i){pattern}')
      def command_match(desc):
        desc = ' '.join([desc.name, desc.brief] + desc.aliases)
        return re.match(rx, desc)
      commands = list(filter(command_match, all_commands))
    return self.do_commands(commands, env)

  def do_commands(self, commands, env):
    if self.opt('plain', self.opt('p', False)) or len(self.args) == 1:
      return self.do_commands_plain(commands, env)
    if self.opt('raw', self.opt('r', False)):
      return self.do_commands_raw(commands, env)
    return self.do_commands_table(commands, env)

  def do_commands_table(self, commands, env):
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

    section = None
    for desc in commands:
      if section != desc.section:
        section = desc.section
        row('', '')
        row('', f'---- {section} ----')
        row('', '')
      row(desc.name, desc.brief)
      row('', desc.synopsis)
      if desc.aliases:
        row('', 'Aliases: ' + ', '.join(desc.aliases))
      if self.opt(('verbose', 'v')):
        row('', '')
        for text in desc.detail:
          row('', text)
        emit_opts('Arguments:', desc.args)
        emit_opts('Options:', desc.opts)
        row('', '')
      row('', '')
    return MarkdownOut().xform(tab, env)

  def do_commands_raw(self, commands, env):
    return JsonOut().xform(to_dict(commands), env)

  def do_commands_plain(self, commands, _env):
    lines = []
    def row(*cols):
      lines.append(''.join(cols))
    def emit_opts(title, opts):
      if opts:
        row('', '')
        row('', title)
        row('', '')
        table = list(opts.items())
        for line in tabulate(table, tablefmt="presto").splitlines():
          line = line[1:]
          row('  ', line)
    attrs = list(DEFAULTS.keys())
    for desc in commands:
      # row('', "'''")
      row('', desc.name, ' - ', desc.brief)
      row('', '')
      row('  ', desc.synopsis)
      if desc.aliases:
        row('', '')
        row('', 'Aliases: ' + ', '.join(desc.aliases))
      for text in desc.detail:
        row('', text)
      emit_opts('Arguments:', desc.args)
      emit_opts('Options:', desc.opts)
      if desc.examples:
        row('', '')
        row('', 'Examples:')
        row('', '')
        for example in desc.examples:
          for comment in example.comments:
            row('', "# ", comment)
          row('', '$ ', example.command)
          row('', '')
      # row('', "'''")
      if attrs and self.opt('verbose', self.opt('v')):
        row('', '')
        for attr in attrs:
          val = getattr(desc, attr)
          if val:
            row(f':{attr}={val}')
      if len(commands) > 1:
        row('', '                    ==========================================================')
        row('', '')
    return '\n'.join(lines + [''])
