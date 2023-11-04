import pandas as pd
from .format import MarkdownOut
from .command import Command, command, descriptors

@command('help', [],
         synopsis="This help document.")
class Help(Command):
  def xform(self, _inp, env):
    tab = pd.DataFrame(columns=['command', 'synposis', 'argument', 'description'])
    for desc in descriptors():
      row = [
        desc['name'],
        desc['synopsis'],
        '',
        '',
      ]
      tab.loc[len(tab.index)] = row
      if desc['aliases']:
        row = [
          '',
          'Aliases: ' + ', '.join(desc['aliases']),
          '',
          '',
        ]
        tab.loc[len(tab.index)] = row
      for arg, doc in desc['args'].items():
        row =  [
          '',
          '',
          arg,
          doc,
        ]
        tab.loc[len(tab.index)] = row
      for opt, doc in desc['opts'].items():
        row =  [
          '',
          '',
          "--" + opt,
          doc,
        ]
        tab.loc[len(tab.index)] = row
    return MarkdownOut().xform(tab, env)
