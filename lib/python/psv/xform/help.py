from . import base
from .format import MarkdownOut
import pandas as pd

class Help(base.Base):
  def xform(self, inp):
    df = pd.DataFrame(columns=['command', 'aliases', 'synopsis', 'argument', 'description'])
    for desc in base.descriptors():
      row = [
        desc['name'],
        ', '.join(desc['aliases']),
        desc['synopsis'],
        '',
        '',
      ]
      df.loc[len(df.index)] = row
      for arg, doc in desc['args'].items():
        row =  [
          '',
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
          '',
          "--" + opt,
          doc,
        ]
        df.loc[len(df.index)] = row
    return MarkdownOut().xform(df)
base.register(Help, 'help', [],
         synopsis="THis help document.")
