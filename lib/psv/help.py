import re
import pandas as pd
import tabulate
from devdriven.to_dict import to_dict
from devdriven.cli.application import app, DEFAULTS
from .command import Command, section, command
from .formats import MarkdownOut, JsonOut

section('Documentation')

@command
class Help(Command):
  '''
  help - This help document.

  --verbose, -v   |  Show more detail.
  --plain, -p     |  Show plain docs.
  --raw, -r       |  Raw detail.
  '''
  def xform(self, _inp, env):
    tabulate.PRESERVE_WHITESPACE = True
    commands = all_commands = app.descriptors_by_sections()
    if self.args:
      pattern = '|'.join([f' {arg} ' for arg in self.args])
      rx = re.compile(f'(?i).*({pattern}).*')

      def match_precise(desc):
        slug = '  '.join(['', desc.name, desc.brief] + desc.aliases + [''])
        return re.match(rx, slug)

      def match_soft(desc):
        slug = '  '.join(['', desc.brief, ''])
        return re.match(rx, slug)

      commands = list(filter(match_precise, all_commands))
      if not commands:
        commands = list(filter(match_soft, all_commands))
    return self.do_commands(commands, env)

  def do_commands(self, commands, env):
    if self.opt('raw', False):
      return self.do_commands_raw(commands, env)
    if self.opt('plain', False) or len(self.args) == 1:
      return self.do_commands_plain(commands, env)
    return self.do_commands_table(commands, env)

  def do_commands_table(self, commands, env):
    tab = pd.DataFrame(columns=['command', 'description'])

    def row(*cols):
      tab.loc[len(tab.index)] = cols

    def emit_opts(title, items):
      if items:
        row('', '')
        row('', title)
        row('', '')
        rows = self.items_to_rows(items)
        for line in tabulate.tabulate(rows, tablefmt="presto").splitlines():
          row('', '  ' + line)

    sec = None
    for desc in commands:
      if sec != desc.section:
        sec = desc.section
        row('  ---------', '')
        row('   Section ', f'-------- {sec} --------')
        row('  ---------', '')
        row('', '')
      row(desc.name, desc.brief)
      row('', '')
      row('', '  ' + desc.synopsis)
      if desc.aliases:
        row('', '')
        row('', 'Aliases: ' + ', '.join(desc.aliases))
      if self.opt('verbose'):
        if desc.detail:
          row('', '')
          for text in desc.detail:
            row('', text)
        emit_opts('Arguments:', self.args_table(desc))
        emit_opts('Options:', self.opts_table(desc))
      row('', '')
    return MarkdownOut().xform(tab, env)

  def do_commands_raw(self, commands, env):
    return JsonOut().xform(to_dict(commands), env)

  def do_commands_plain(self, commands, _env):
    lines = []

    def row(*cols):
      lines.append(''.join(cols))

    def emit_opts(title, items):
      if items:
        row('', '')
        row('', title)
        row('', '')
        rows = self.items_to_rows(items)
        for line in tabulate.tabulate(rows, tablefmt="presto").splitlines():
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
      if desc.detail:
        row('', '')
        for text in desc.detail:
          row('', text)
      emit_opts('Arguments:', self.args_table(desc))
      emit_opts('Options:', self.opts_table(desc))
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
        row('', '')
        row('==========================================================')
        row('', '')
    return '\n'.join(lines + [''])

  def items_to_rows(self, items):
    rows = []
    for name, desc in list(items):
      item_rows = []
      for desc_line in desc.split('.  '):
        if desc_line:
          desc_line = re.sub(r'\.\. *$', '.', desc_line + '.')
          item_rows.append([name, desc_line])
          name = ''
      if len(item_rows) > 1 and rows:
        rows.append(['', ''])
      rows.extend(item_rows)
    return rows

  def args_table(self, desc):
    return desc.options.arg_by_name.items()

  def opts_table(self, desc):
    return [opt.table_row() for opt in desc.options.opts]
