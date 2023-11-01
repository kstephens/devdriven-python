import logging
import json
import sys
import os
import devdriven.cli
from devdriven.to_dict import to_dict
from . import command, pipeline, io, format, process, metadata, repl, example, help

class Main(devdriven.cli.Main):
  def __init__(self):
    super().__init__()
    self.prog_name = 'tsv'
    self.env = {}

  def parse_argv(self, argv):
    if not argv:
      argv = ['help']
    return super().parse_argv(argv)

  def make_command(self, argv):
    cmd = Main.MainCommand().set_main(self).parse_argv(argv)
    cmd.env = self.env
    return cmd

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
      self.env = None

    def parse_argv(self, argv):
      self.pipeline = self.parse_pipeline(argv)
      return self

    def parse_pipeline(self, argv):
      pipe = pipeline.Pipeline().set_main(self.main).set_name('main').parse_argv(argv)
      if pipe.xforms:
        if not isinstance(pipe.xforms[0], io.IoIn):
          pipe.xforms.insert(0, io.IoIn())
        if not isinstance(pipe.xforms[-1], io.IoOut):
          pipe.xforms.append(io.IoOut())
      return pipe

    def exec(self):
      self.env.update({'now': self.main.now})
      inp = None  # ???
      return self.pipeline.xform(inp, self.env)


if __name__ == '__main__':
  instance = Main()
  instance.prog_path = os.environ['prog_path']
  sys.exit(instance.run(sys.argv).exit_code)
