#!/usr/bin/env python3.10
import logging as log
import json
import re
import sys
from datetime import datetime
from devdriven.util import not_implemented
from devdriven.to_dict import to_dict
from pathlib import Path
import urllib3

class Main:
  def __init__(self):
    self.stdin = sys.stdin
    self.stdout = sys.stdout
    self.http = urllib3.PoolManager()
    self.now = datetime.now()
    self.prog_name = None
    self.argv0 = None
    self.prog_path = None
    self.bin_dir = None
    self.root_dir = None
    self.argv = []
    self.commands = []
    self.results = []
    self.errors = []
    self.output = None
    self.exit_code = None

  def run(self, argv):
    log.basicConfig(level=log.INFO)
    self.set_argv(argv)
    self.parse_argv(argv[1:])
    self.results = self.exec()
    self.output = self.prepare_output(self.results)
    self.emit_output(self.output)
    if self.errors and not self.exit_code:
      self.exit_code = 1
    if not self.exit_code:
      self.exit_code = 0
    return self

  def set_argv(self, argv):
    self.argv = argv.copy()
    self.argv0 = argv[0]
    if not self.prog_path:
      self.prog_path = str(Path(self.argv0).absolute())
    if not self.bin_dir:
      self.bin_dir = str(Path(self.prog_path).parent)
    if not self.root_dir:
      self.root_dir = str(Path(self.bin_dir) / '..')
    return self

  def parse_argv(self, argv):
    self.commands = self.parse_commands(argv)
    return self

  def exec(self):
    return self.exec_commands(self.commands)

  def parse_commands(self, argv):
    commands = []
    command_argv = []
    while argv:
      arg = argv.pop(0)
      (separated, last_arg) = self.arg_is_command_separator(arg)
      if separated and last_arg:
        command_argv.append(last_arg)
        self.build_command(commands, command_argv)
        command_argv = []
      else:
        command_argv.append(arg)
    self.build_command(commands, command_argv)
    return commands

  def build_command(self, commands, argv):
    if argv:
      command = self.make_command(argv)
      if not command:
        return
      command.main = self
      commands.append(command)
      return command

  def exec_commands(self, commands):
    results = [self.exec_command(command) for command in commands]
    errors = [(command, self.error_repr(error)) for command, ok, error in results if not ok]
    self.errors.extend(errors)
    result = [(command, rtn) for command, ok, rtn in results if ok]
    return result

  def exec_command(self, command):
    if self.capture_exceptions(command):
      try:
        return (command, True, command.exec())
      except Exception as exc:
        log.error(exc)
        return (command, False, exc)
    else:
      return (command, True, command.exec())

  def capture_exceptions(self, _command):
    return False

  def prepare_output(self, results):
    errors = [[command.name, self.error_repr(error)] for (command, error) in self.errors]
    result = [[command.name, result] for (command, result) in results]
    return {"errors": errors, "result": result}

  def emit_output(self, output):
    output = to_dict(output)
    json.dump(output, fp=self.output_file())
    return output

  def output_file(self):
    return sys.stdout

  def error_repr(self, err):
    return to_dict(err)

  # OVERRIDE:
  def make_command(self, _argv):
    not_implemented()
    return False

  # OVERRIDE:
  def arg_is_command_separator(self, arg):
    if mtch := re.match(r'^(.+),$', arg):
      return (True, mtch.group(1))
    return (False, arg)
