#!/usr/bin/env python3.11
from typing import Any, Optional, Self, Tuple, List, Dict, IO, NoReturn
import logging as log
import json
import re
import sys
from pathlib import Path
from datetime import datetime
from devdriven.cli.types import Argv
from devdriven.util import not_implemented
from devdriven.to_dict import to_dict
import urllib3
from .command import Command


class Main:
    stdin: IO
    stdout: IO
    stderr: IO
    config: Any
    argv0: str
    argv: Argv
    commands: List[Command]
    results: list
    errors: list
    output: Any
    exit_code: int

    def __init__(self):
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.config = None
        self.http = urllib3.PoolManager()
        self.now = datetime.now()
        self.prog_name = self.prog_path = self.bin_dir = None
        self.root_dir = None
        self.argv0 = None
        self.argv = []
        self.commands = []
        self.results = []
        self.errors = []
        self.output = None
        self.exit_code = None

    def run(self, argv: Argv) -> Self:
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

    def set_argv(self, argv) -> Self:
        self.argv = argv.copy()
        self.argv0 = argv[0]
        if not self.prog_path:
            self.prog_path = str(Path(self.argv0).absolute())
        if not self.bin_dir:
            self.bin_dir = str(Path(self.prog_path).parent)
        if not self.root_dir:
            self.root_dir = str(Path(self.bin_dir) / "..")
        return self

    def parse_argv(self, argv) -> Self:
        self.commands = self.parse_commands(argv)
        return self

    def exec(self) -> Any:
        return self.exec_commands(self.commands)

    def parse_commands(self, argv: Argv) -> List[Command]:
        commands: List[Command] = []
        command_argv: Argv = []
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

    def build_command(self, commands: list, argv: Argv) -> Optional[Command]:
        if argv:
            if command := self.make_command(argv):
                command.main = self
                commands.append(command)
            return command
        return None

    def exec_commands(self, commands: List[Command]) -> Any:
        results = [self.exec_command(command) for command in commands]
        errors = [
            (command, self.error_repr(error))
            for command, ok, error in results
            if not ok
        ]
        self.errors.extend(errors)
        result = [(command, rtn) for command, ok, rtn in results if ok]
        return result

    def exec_command(self, command) -> Tuple[Any, bool, Any]:  #
        if self.capture_exceptions(command):
            try:
                return (command, True, command.exec())
            # pylint: disable-next=broad-except
            except Exception as exc:
                log.error(exc)
                return (command, False, exc)
        else:
            return (command, True, command.exec())

    def capture_exceptions(self, _command) -> bool:
        return False

    def prepare_output(self, results) -> Dict[str, Any]:
        errors = [
            [command.name, self.error_repr(error)] for (command, error) in self.errors
        ]
        result = [[command.name, result] for (command, result) in results]
        return {"errors": errors, "result": result}

    def emit_output(self, output: Any) -> Any:
        output = to_dict(output)
        json.dump(output, fp=self.output_file(), indent=2)
        return output

    def output_file(self) -> IO:
        return sys.stdout

    def error_repr(self, err: Exception) -> Any:
        return to_dict(err)

    # OVERRIDE:
    def make_command(self, _argv: Argv) -> Any:
        not_implemented()

    #    return None

    # OVERRIDE:
    def arg_is_command_separator(self, arg: str) -> Tuple[bool, str]:
        if mtch := re.match(r"^(.+),$", arg):
            return (True, mtch.group(1))
        return (False, arg)

    def fatal(self, msg: str, exit_code: Optional[int] = None) -> NoReturn:
        self.exit_code = exit_code or 1
        print(msg, file=self.stderr)
        sys.exit(self.exit_code)
