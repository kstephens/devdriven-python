#!/usr/bin/env python3.10
import logging as log
import json
import re
import sys
from datetime import datetime
import urllib3
from .command import Command

# from icecream import ic, install
#install()
#ic.configureOutput(includeContext=True)

class Main:
  def __init__(self):
    self.http = urllib3.PoolManager()
    self.now = datetime.now()
    self.prog_name = None
    self.argv = []
    self.commands = []
    self.results = []
    self.errors = []
    self.output = None
    self.exit_code = None

  def run(self, argv):
    log.basicConfig(level=log.INFO)
    # self.prog_name = argv.pop(0)
    self.argv = argv.copy()
    self.commands = self.parse_commands(argv.copy())
    self.results = self.run_commands(self.commands)
    self.output = self.prepare_output(self.results)
    self.emit_output(self.output)
    if self.errors and not self.exit_code:
      self.exit_code = 1
    if not self.exit_code:
      self.exit_code = 0
    return self

  def parse_commands(self, argv):
    commands = []
    command_argv = []
    while argv:
      arg = argv.pop(0)
      (separated, last_arg) = self.arg_is_command_separator(arg)
      if separated and last_arg:
        command_argv.append(last_arg)
        commands.append(self.make_command(command_argv))
        command_argv = []
      else:
        command_argv.append(arg)
    if command_argv:
      commands.append(self.make_command(command_argv))
    return commands

  def run_commands(self, commands):
    results = [self.run_command(command) for command in commands]
    errors = [(command, self.error_string(error)) for command, ok, error in results if not ok]
    self.errors.extend(errors)
    result = [(command, rtn) for command, ok, rtn in results if ok]
    return result

  def run_command(self, command):
    try:
      return (command, True, command.run())
    except Exception as exc:
      log.error(exc)
      return (command, False, exc)

  def prepare_output(self, results):
    errors = [[command.name, self.error_string(error)] for (command, error) in self.errors]
    result = [[command.name, result] for (command, result) in results]
    return {"errors": errors, "result": result}

  def emit_output(self, output):
    json.dump(output, fp=sys.stdout)
    return output

  def error_string(self, err):
    if hasattr(err, 'message'):
      return err.message
    return str(err)

  # OVERRIDE:
  def make_command(self, argv):
    raise Exception("make_command(self, argv): not implemented")

  # OVERRIDE:
  def arg_is_command_separator(self, arg):
    if mtch := re.match(r'^(.*),$', arg):
      return (True, mtch.group(1))
    return (False, arg)
