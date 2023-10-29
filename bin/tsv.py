#!/usr/bin/env python3.10
import sys
import devdriven.cli

class Tsv(devdriven.cli.Main):
  def make_command(self, argv):
    return Tsv.RootCommand(self).parse_argv(argv)

  def arg_is_command_separator(self, arg):
    return (False, arg)

  class RootCommand(devdriven.cli.Command):
    def exec(self):
      return "RootCommand: OK"

if __name__ == "__main__":
  sys.exit(Tsv().run(sys.argv).exit_code)
