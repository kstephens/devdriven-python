from . import base
from .format import MarkdownOut
import pandas as pd

class Help(base.Base):
  def xform(self, inp):
    df = pd.DataFrame(columns=['command', 'synposis', 'argument', 'description'])
    for desc in base.descriptors():
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
    return MarkdownOut().xform(df)
base.register(Help, 'help', [],
         synopsis="This help document.")
