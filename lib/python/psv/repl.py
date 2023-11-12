from pprint import pprint
from devdriven.repl import start_repl
from .command import Command, command

@command()
class Repl(Command):
  '''
  repl - Start an interactive REPL.

  `inp` : Input Pandas DataFrame.
  `out` : Copy of `inp`.

  '''
  def xform(self, inp, env):
    print('========================================')
    print('env:')
    pprint(env)
    print('')
    print('inp:')
    print(inp)
    print('========================================\n')
    out = inp.copy()
    bindings = globals()
    bindings.update(locals())
    start_repl(bindings)
    return out
