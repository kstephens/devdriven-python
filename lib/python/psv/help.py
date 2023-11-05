import re
import pandas as pd
from .format import MarkdownOut
from .command import Command, command, descriptors

@command('help', [],
         synopsis="This help document.")
class Help(Command):
  def xform(self, _inp, env):
    tab = pd.DataFrame(columns=['command', 'synposis', 'argument', 'description'])
    def row(*cols):
      tab.loc[len(tab.index)] = cols
    commands = all_commands = descriptors()
    if self.args:
      commands = filter(lambda cmd: self.command_matches(cmd, self.argv[0]), all_commands)
    for desc in commands:
      row(desc['name'], desc['synopsis'], '', '')
      if desc['aliases']:
        row('', 'Aliases: ' + ', '.join(desc['aliases']), '', '')
      for arg, doc in desc['args'].items():
        row('', '', arg, doc)
      for opt, doc in desc['opts'].items():
        row('', '', "--" + opt, doc)
    return MarkdownOut().xform(tab, env)
  def command_matches(self, desc, pattern):
    desc = '|'.join([desc['name'], desc['synopsis']] + desc['aliases'])
    return re.match(re.compile(f'(?i).*{pattern}.*'), desc)
