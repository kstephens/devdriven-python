from typing import Any, Self, Tuple, IO
import logging
import json
import sys
import os
import devdriven.cli
from devdriven.cli.types import Argv
from devdriven.to_dict import to_dict
from devdriven.random import set_seed
from . import pipeline, io

class Main(devdriven.cli.Main):
  def __init__(self):
    if seed := os.environ.get('PSV_RAND_SEED'):
      set_seed(seed)
    super().__init__()
    self.prog_name = 'psv'
    self.env = {}
    logging.getLogger("urllib3").setLevel(logging.WARNING)

  def parse_argv(self, argv: Argv):
    if not argv:
      argv = ['help']
    return super().parse_argv(argv)

  def make_command(self, argv: Argv) -> devdriven.cli.Command:
    cmd = Main.MainCommand()
    cmd.main = self
    cmd.parse_argv(argv)
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
    obj = pipeline.Pipeline()
    obj.main = self
    obj.name = name
    return obj.parse_argv(argv)

  class MainCommand(devdriven.cli.Command):
    def __init__(self, *args):
      super().__init__(*args)
      self.prog_name = 'psv'
      self.name = 'main'
      self.pipeline = None
      self.env = None

    def parse_argv(self, argv: Argv) -> Self:
      # pylint: disable-next=no-member
      pipe = self.main.parse_pipeline('main', argv)
      if pipe.xforms:
        if not isinstance(pipe.xforms[0], io.IoIn):
          in_cmd = io.IoIn()
          in_cmd.main = self.main
          pipe.xforms.insert(0, in_cmd)
        if not isinstance(pipe.xforms[-1], io.IoOut):
          out_cmd = io.IoOut()
          out_cmd.main = self.main
          pipe.xforms.append(out_cmd)
      self.pipeline = pipe
      return self

    def exec(self) -> Any:
      self.env.update({
        # pylint: disable-next=no-member
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
