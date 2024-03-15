from typing import Iterable, List
import re
import html
from dataclasses import dataclass, field
import pandas as pd  # type: ignore
import tabulate  # type: ignore
# from icecream import ic
from devdriven.to_dict import to_dict
from devdriven.cli.application import app
from devdriven.cli.descriptor import Descriptor
from devdriven.cli.option import Option
from .command import Command, section, command
from .markdown import MarkdownOut
from .json import JsonOut
from .example import ExampleRegistry

section('Documentation', 200)

@command
class Help(Command):
  '''
  help - This help document.

  --verbose, -v   |  Show more detail.
  --list, -l      |  List commands.
  --plain, -p     |  Show plain docs.
  --raw, -r       |  Raw detail.
  --sections, -s  |  List sections.
  --markdown      |  Emit Markdown.
  '''
  def xform(self, _inp, env):
    tabulate.PRESERVE_WHITESPACE = True

    if self.opt('sections'):
      return self.do_sections(app.sections, env)

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

    all_sdc = ExampleRegistry(self.main).all_examples()
    all_desc = {sdc.descriptor.name: sdc.descriptor for sdc in all_sdc}
    for cmd in commands:
      cmd.examples = all_desc.get(cmd.name, cmd).examples

    return self.do_commands(commands, env)

  def do_sections(self, sections, env):
    tab = pd.DataFrame(columns=['section', 'command', 'brief'])

    def row(*cols):
      tab.loc[len(tab.index)] = cols

    for (name, descs) in [(s.name, s.descriptors) for s in sections]:
      name_last = None
      for desc in descs:
        if name_last == name:
          name = ''
        name_last = name
        row(name, desc.name, desc.brief)

    return MarkdownOut().xform(tab, env)

  def do_commands(self, commands, env):
    if self.opt('raw', False):
      return self.do_commands_raw(commands, env)
    if self.opt('markdown', False):
      return self.do_commands_markdown(commands, env)
    if self.opt('plain', False) or len(self.args) == 1:
      return self.do_commands_plain(commands, env)
    if self.opt('list', False):
      return self.do_commands_list(commands, env)
    return self.do_commands_table(commands, env)

  def do_commands_list(self, commands, env):
    tab = pd.DataFrame(columns=['command', 'description'])

    def row(*cols):
      tab.loc[len(tab.index)] = cols
    for desc in commands:
      row(desc.name, desc.brief)
    return MarkdownOut().xform(tab, env)

  def do_commands_table(self, commands, env):
    verbose = self.opt('verbose', self.opt('v'))
    fmt = FormatTable(show_metadata=verbose, show_example_output=verbose)
    fmt.commands(commands)
    return MarkdownOut().xform(fmt.output(), env)

  def do_commands_raw(self, commands, env):
    return JsonOut().xform(to_dict(commands), env)

  def do_commands_plain(self, commands, _env):
    verbose = self.opt('verbose', self.opt('v'))
    fmt = FormatText(show_metadata=verbose, show_example_output=verbose)
    fmt.commands(commands)
    return fmt.output()

  def do_commands_markdown(self, commands, _env):
    verbose = self.opt('verbose', self.opt('v'))
    fmt = FormatMarkdown(show_examples=True, show_example_output=verbose)
    fmt.commands(commands)
    return fmt.output()

#######################################

@dataclass
class Format():
  rows: List[str] = field(default_factory=list)
  show_section: bool = field(default=True)
  show_examples: bool = field(default=True)
  show_example_output: bool = field(default=False)
  show_metadata: bool = field(default=False)

  def commands(self, descs):
    sec = None
    for desc in descs:
      if self.show_section:
        if sec != desc.section:
          sec = desc.section
          self.section(desc.section)
      self.command(desc)
      if self.show_metadata:
        self.metadata(desc)
      if len(descs) > 1:
        self.hrule()

  def section(self, name):
    self.row('   Section ', f'-------- {name} --------')
    self.row('', '')

  def command(self, desc):
    row = self.row
    self.command_begin(desc)
    self.brief(desc)
    row()
    self.synopsis(desc)
    if desc.aliases:
      row()
      self.aliases(desc)
    if desc.detail:
      row()
      for text in desc.detail:
        row('', text)
    self.emit_opts('Arguments:', args_table(desc))
    self.emit_opts('Options:', opts_table(desc))
    if desc.examples:
      row()
      row('', 'Examples:')
      row()
      if self.show_examples:
        for example in desc.examples:
          self.code_begin()
          for comment in example.comments:
            row('', "# " + comment)
          row('', '$ ' + example.command)
          if self.show_example_output:
            row('', example.output)
          self.code_end()
          row()
    self.command_end(desc)

  def command_begin(self, _desc):
    return None

  def command_end(self, _desc):
    self.row()

  def brief(self, desc):
    self.row(self.code(desc.name), f' - {desc.brief}')

  def synopsis(self, desc):
    self.row('  ', desc.synopsis)

  def aliases(self, desc):
    self.row('Aliases: ', ', '.join(map(self.code, desc.aliases)))

  def metadata(self, desc):
    row = self.row
    if attrs := list(desc.metadata.keys()):
      row()
      for attr in attrs:
        val = getattr(desc, attr, None)
        if val:
          row('', f':{attr}={val}')

  def emit_opts(self, title, items):

    def row(line):
      self.row('', '  ' + line)
    self.table(title, items, row)

  def table(self, title, items, table_row, **kwargs):
    row = self.row
    if items:
      row()
      row('', title)
      row()
      rows = items_to_rows(items)
      lines = tabulate.tabulate(rows, **kwargs).splitlines()
      width = max(map(len, lines))
      for line in lines:
        line = line + ' ' * (width - len(line))
        table_row(line)

  def code_begin(self, _lang=''):
    return

  def code_end(self):
    return

  def code(self, x):
    return str(x)

  def hrule(self, chars='-'):
    self.row('', chars * 58)
    self.row()

  def row(self, *cols):
    if not cols:
      cols = ('', '')
    self.rows.append(''.join(map(str, cols)))

  def output(self):
    return '\n'.join([str(row).rstrip() for row in self.rows] + [''])

class FormatMarkdown(Format):
  def section(self, name):
    self.row(f'# {name}')
    self.row()

  def synopsis(self, desc):
    self.code_begin()
    self.row('', desc.synopsis)
    self.code_end()

  def command_begin(self, desc):
    self.row(f'## {self.code(desc.name)}')
    self.row()

  def emit_opts(self, title, items):
    separator = False

    def opt_line(row):
      nonlocal separator
      if not separator:
        separator = re.sub(r'[^|]', '-', row)
        separator = re.sub(r'-\|-', ' | ', separator)
        separator = '| ' + separator + ' |'
        header = re.sub(r'-', ' ', separator)
        self.row(header)
        self.row(separator)
      self.row(f'| {row} |')

    def comma_code(option):
      return ', '.join([self.code(x) for x in re.split(r', ', option)])

    items = [(comma_code(key), html.escape(val)) for key, val in items]
    self.table(title, items, opt_line, tablefmt="presto")

  def code_begin(self, lang='NONE'):
    self.row('```', lang)

  def code_end(self):
    self.row('```')
    self.row()

  def code(self, x):
    return f'`{x}`'


class FormatText(Format):
  def section(self, name):
    self.row('', f'  Section {name}')
    self.row()

  def synopsis(self, desc):
    self.row('  ', desc.synopsis)

  def emit_opts(self, title, items):

    def row(line):
      self.row('  ', line[1:])
    self.table(title, items, row, tablefmt="presto")

class FormatTable(Format):
  def section(self, name):
    row = self.row
    title = f'         {name}         '
    header = '=' * len(title)
    row('  ===========  ', '  ' + header)
    row('    Section    ', '  ' + title)
    row('  ===========  ', '  ' + header)
    row('', '')

  def synopsis(self, desc):
    self.row('', '  ' + desc.synopsis)

  def brief(self, desc):
    self.row(desc.name, desc.brief)

  def aliases(self, desc):
    self.row('', 'Aliases: ' + ', '.join(desc.aliases))

  def row(self, *cols):
    if not cols:
      cols = ('', '')
    self.rows.append(cols)

  def emit_opts(self, title, items):

    def row(line):
      self.row('', '  ' + line)
    self.table(title, items, row, tablefmt="presto")

  def output(self):
    tab = pd.DataFrame(columns=['command', 'description'])
    for row in self.rows:
      assert len(row) == 2
      tab.loc[len(tab.index)] = row
    return tab

#########################################

def items_to_rows(items):
  rows = []
  for name, desc in list(items):
    item_rows = []
    for desc_line in desc.strip().split('.  '):
      desc = desc.strip()
      if desc_line:
        desc_line = re.sub(r'\.\. *$', '.', desc_line + '.').strip()
        if name and desc_line:
          item_rows.append([name, desc_line])
        name = ''
    if len(item_rows) > 1 and rows:
      rows.append(('', ''))
    rows.extend(item_rows)
  return rows

def args_table(desc: Descriptor) -> Iterable:
  return desc.options.arg_by_name.items()

def opts_table(desc: Descriptor) -> List[List[str]]:
  return [opt_row(opt) for opt in desc.options.opts]

def opt_row(opt: Option) -> List[str]:
  return [opt.synopsis(), opt.description]
