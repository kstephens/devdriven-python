from pprint import pprint
from devdriven.repl import start_repl
from .command import Command, section, command

section('Expression Evaluation', 70)

@command
class Repl(Command):
  '''
  repl - Start an interactive REPL.

  `inp`  |  Input table.
  `out`  |  Output table; copy of `inp`.

  '''
  def xform(self, inp, env):
    print('========================================')
    print('env:')
    pprint(env)
    print('')
    print('inp:')
    print(inp)
    print('========================================\n')
    out = inp
    if getattr(inp, 'copy', False):
      out = inp.copy()
    bindings = globals()
    bindings.update(locals())
    start_repl(bindings)
    return out
