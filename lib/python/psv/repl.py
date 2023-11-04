from pprint import pprint
from devdriven.repl import start_repl
from .command import Command, command

@command('repl', [''],
         synopsis="Start an interactive REPL.",
         args={})
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
