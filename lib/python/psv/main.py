import logging
import json
import sys
import devdriven.cli
from devdriven.to_dict import to_dict
from .xform import pipeline

class Main(devdriven.cli.Main):
  def __init__(self):
    super().__init__()
    self.prog_name = 'tsv'

  def make_command(self, argv):
    return Main.MainCommand().parse_argv(argv)

  def arg_is_command_separator(self, arg):
    return (False, arg)

  def emit_output(self, output):
    output = to_dict(output)
    logging.debug(json.dumps(output, indent=2))
    return output

  def output_file(self):
    return sys.stderr

  class MainCommand(devdriven.cli.Command):
    def __init__(self, *args):
      super().__init__(*args)
      self.prog_name = 'tsv'
      self.name = 'main'
      self.pipeline = None

    def parse_argv(self, argv):
      self.pipeline = self.parse_pipeline(argv)
      return self

    def parse_pipeline(self, argv):
      return pipeline.Pipeline().set_main(self.main).set_name('main').parse_argv(argv)

    def exec(self):
      inp = None # ???
      return self.pipeline.xform(inp)
