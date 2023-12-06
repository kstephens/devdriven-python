import code
import readline
import rlcompleter
import sys
from pprint import pprint

# https://stackoverflow.com/questions/50917938/enabling-console-features-with-code-interact
# https://stackoverflow.com/questions/17248383/pretty-print-by-default-in-python-repl

def start_repl(bindings):
  readline_completer_save = readline.get_completer()
  sys_displayhook_save = sys.displayhook
  try:
    readline.set_completer(rlcompleter.Completer(bindings).complete)
    readline.parse_and_bind("tab: complete")
    # pylint: disable-next=exec-used
    sys.displayhook = lambda x: exec(['_=x; pprint(x)','pass'][x is None])
    return code.InteractiveConsole(locals=bindings).interact()
  finally:
    sys.displayhook = sys_displayhook_save
    readline.set_completer(readline_completer_save)
