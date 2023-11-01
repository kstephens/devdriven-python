import sys
import os
from pprint import pprint
from devdriven.repl import start_repl
from collections import OrderedDict, Counter
from datetime import datetime, timedelta
import pandas as pd
from devdriven.util import chunks, get_safe
from .command import Command, register

class Repl(Command):
  def xform(self, inp, env):
    print('========================================')
    print('env:')
    pprint(env)
    print('')
    print('inp:')
    print(inp)
    print('========================================\n')
    out = inp
    vars = globals()
    vars.update(locals())
    start_repl(vars)
    return out
register(Repl, 'repl', [''],
         synopsis="Start an interactive REPL.",
         args={})

