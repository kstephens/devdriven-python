import code
import readline
import rlcompleter
from io import StringIO
from collections import OrderedDict, Counter
from datetime import datetime, timedelta
import pandas as pd
# from devdriven.util import chunks, get_safe
from .command import Command, register

class Repl(Command):
  def xform(self, inp, env):
    readline_completer_save = readline.get_completer()
    try:
      print('env:')
      print(repr(env))
      print('inp:')
      print(inp)
      out = inp
      vars = globals()
      vars.update(locals())
      readline.set_completer(rlcompleter.Completer(vars).complete)
      readline.parse_and_bind("tab: complete")
      code.InteractiveConsole(locals=vars).interact()
    finally:
      readline.set_completer(readline_completer_save)
    return out
register(Repl, 'repl', [''],
         synopsis="Start an interactive REPL.",
         args={})

