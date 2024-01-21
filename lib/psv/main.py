from typing import Any, Self, Tuple, IO
import logging
import json
import sys
import os
import devdriven.cli
from devdriven.cli.types import Argv
from devdriven.to_dict import to_dict
from . import pipeline, io

class Main(devdriven.cli.Main):
  def __init__(self):
    super().__init__()
    self.prog_name = 'psv'
    self.env = {}
    logging.getLogger("urllib3").setLevel(logging.WARNING)

  def parse_argv(self, argv: Argv):
    if not argv:
      argv = ['help']
    return super().parse_argv(argv)

  def make_command(self, argv: Argv) -> devdriven.cli.Command:
    cmd = Main.MainCommand().set_main(self).parse_argv(argv)
    cmd.env = self.env
    return cmd

  def arg_is_command_separator(self, arg: str) -> Tuple[bool, str]:
    return (False, arg)

  def emit_output(self, output):
    output = to_dict(output)
    logging.debug(json.dumps(output, indent=2))
    return output

  def output_file(self) -> IO:
    return self.stdout

  def parse_pipeline(self, name: str, argv: Argv) -> pipeline.Pipeline:
    return pipeline.Pipeline().set_main(self).set_name(name).parse_argv(argv)

  class MainCommand(devdriven.cli.Command):
    def __init__(self, *args):
      super().__init__(*args)
      self.prog_name = 'psv'
      self.name = 'main'
      self.pipeline = None
      self.env = None

    def parse_argv(self, argv: Argv) -> Self:
      pipe = self.main.parse_pipeline('main', argv)
      if pipe.xforms:
        if not isinstance(pipe.xforms[0], io.IoIn):
          pipe.xforms.insert(0, io.IoIn())
        if not isinstance(pipe.xforms[-1], io.IoOut):
          pipe.xforms.append(io.IoOut())
      self.pipeline = pipe
      return self

    def exec(self) -> Any:
      self.env.update({
        'now': self.main.now,
        'history': [],
        'xform': {},
        'Content-Type': None,
        'Content-Encoding': None,
      })
      return self.pipeline.xform(None, self.env)


if __name__ == '__main__':
  instance = Main()
  instance.prog_path = os.environ['PSV_PROG_PATH']
  sys.exit(instance.run(sys.argv).exit_code)
