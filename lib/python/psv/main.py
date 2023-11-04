import logging
import json
import sys
import os
import devdriven.cli
from devdriven.to_dict import to_dict
from . import pipeline, io

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

  def parse_pipeline(self, name, argv):
    pipe = pipeline.Pipeline().set_main(self).set_name(name).parse_argv(argv)
    return pipe

  class MainCommand(devdriven.cli.Command):
    def __init__(self, *args):
      super().__init__(*args)
      self.prog_name = 'tsv'
      self.name = 'main'
      self.pipeline = None
      self.env = None

    def parse_argv(self, argv):
      pipe = self.main.parse_pipeline('main', argv)
      if pipe.xforms:
        if not isinstance(pipe.xforms[0], io.IoIn):
          pipe.xforms.insert(0, io.IoIn())
        if not isinstance(pipe.xforms[-1], io.IoOut):
          pipe.xforms.append(io.IoOut())
      self.pipeline = pipe
      return self

    def exec(self):
      self.env.update({
        'Content-Type': None,
        'Content-Encoding': None,
        'history': [],
      })
      self.env.update({'now': self.main.now})
      inp = None  # ???
      return self.pipeline.xform(inp, self.env)


if __name__ == '__main__':
  instance = Main()
  instance.prog_path = os.environ['PSV_PROG_PATH']
  sys.exit(instance.run(sys.argv).exit_code)
