import code
import readline
import rlcompleter
from pprint import pprint
import sys
from io import StringIO
from collections import OrderedDict, Counter
from datetime import datetime, timedelta
import pandas as pd
# from devdriven.util import chunks, get_safe
from .command import Command, register

# https://stackoverflow.com/questions/50917938/enabling-console-features-with-code-interact
# https://stackoverflow.com/questions/17248383/pretty-print-by-default-in-python-repl

def run_repl(vars):
  readline_completer_save = readline.get_completer()
  try:
    readline.set_completer(rlcompleter.Completer(vars).complete)
    readline.parse_and_bind("tab: complete")
    sys.displayhook = lambda x: exec(['_=x; pprint(x)','pass'][x is None])
    return code.InteractiveConsole(locals=vars).interact()
  finally:
    sys.displayhook = sys.__displayhook__
    readline.set_completer(readline_completer_save)

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
    run_repl(vars)
    return out
register(Repl, 'repl', [''],
         synopsis="Start an interactive REPL.",
         args={})

