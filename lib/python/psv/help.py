from . import command
from .format import MarkdownOut
import pandas as pd

class Help(command.Command):
  def xform(self, _inp, env):
    df = pd.DataFrame(columns=['command', 'synposis', 'argument', 'description'])
    for desc in command.descriptors():
      row = [
        desc['name'],
        desc['synopsis'],
        '',
        '',
      ]
      df.loc[len(df.index)] = row
      if desc['aliases']:
        row = [
          '',
          'Aliases: ' + ', '.join(desc['aliases']),
          '',
          '',
        ]
        df.loc[len(df.index)] = row
      for arg, doc in desc['args'].items():
        row =  [
          '',
          '',
          arg,
          doc,
        ]
        df.loc[len(df.index)] = row
      for opt, doc in desc['opts'].items():
        row =  [
          '',
          '',
          "--" + opt,
          doc,
        ]
        df.loc[len(df.index)] = row
    return MarkdownOut().xform(df, env)
command.register(Help, 'help', [],
         synopsis="This help document.")
