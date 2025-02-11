from typing import Iterable, Literal, List, cast  # Union, Dict, Tuple, cast
import platform
import os
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from .util import exec_command, count
from .file import file_nlines, file_md5

DiffOptions = Iterable[str]
DiffLines = List[str]
DiffCode = Literal["=", "+", "-"]
DiffCommand = List[str]


@dataclass
class File:
    path: Path

    @cached_property
    def n_bytes(self) -> int:
        return os.stat(self.path).st_size

    @cached_property
    def n_lines(self) -> int:
        return cast(int, file_nlines(str(self.path)))

    @cached_property
    def md5sum(self) -> str:
        return cast(str, file_md5(str(self.path)))


@dataclass
class Difference:
    code: DiffCode
    line_no: int
    a: str | None
    b: str | None


@dataclass
class Diff:
    a: File
    b: File
    differences: List[Difference]

    @cached_property
    def is_same(self) -> bool:
        return self.a.md5sum == self.b.md5sum or self.change_count == 0

    @cached_property
    def old_count(self) -> int:
        return count(self.differences, lambda d: d.code == "-")

    @cached_property
    def new_count(self) -> int:
        return count(self.differences, lambda d: d.code == "+")

    @cached_property
    def change_count(self) -> int:
        return self.old_count + self.new_count


def diff_files(
    expected_file: str, actual_file: str, *diff_options: DiffOptions
) -> Diff:
    a_file = expected_file if os.path.isfile(expected_file) else "/dev/null"
    b_file = actual_file if os.path.isfile(actual_file) else "/dev/null"
    diff_lines = diff_exec(a_file, b_file, *diff_options)
    diffs = [parse_diff_line(line) for line in diff_lines]
    diffs = [diff for diff in diffs if diff is not None]
    return Diff(
        a=File(Path(expected_file)),
        b=File(Path(actual_file)),
        differences=diffs,
    )


def parse_diff_line(line: str) -> Difference:
    code, line = line[0], line[1:]
    if code == "-":
        return Difference("-", 0, line, None)
    if code == "+":
        return Difference("+", 0, None, line)
    if code == "=":
        return Difference("=", 0, line, line)
    raise ValueError(f"invalid diff code {code!r}")


##############################################


def diff_exec(
    expected_file: str,
    actual_file: str,
    *diff_options,
) -> DiffLines:
    command = DIFF_CMD(expected_file, actual_file, diff_options)
    diff_result = exec_command(
        command, check=False, capture_output=True, encoding="utf8"
    )
    if diff_result.stderr:
        raise Exception(
            f"diff_exec: failed : {diff_result.returncode}"
            f": {command!r} : "
            f"{diff_result.stderr.splitlines()[:5]!r}"
        )
    lines = diff_result.stdout.splitlines()
    if DIFF_FENCES:
        lines = [line for line in lines[2:] if not line.startswith(b"@@ ")]
    return lines


def diff_cmd_gnu(
    expected_file: str,
    actual_file: str,
    diff_options: DiffOptions,
) -> DiffCommand:
    return [
        DIFF_PROG,
        "--minimal",
        "--old-line-format=-\n",
        "--new-line-format=+\n",
        "--unchanged-line-format=",
        *diff_options,
        expected_file,
        actual_file,
    ]


def diff_cmd_bsd(
    expected_file: str,
    actual_file: str,
    diff_options: DiffOptions,
) -> DiffCommand:
    return [
        DIFF_PROG,
        "--minimal",
        "-U",
        "0",
        *diff_options,
        expected_file,
        actual_file,
    ]


if platform.system() == "Darwin":
    if os.path.isfile("/opt/homebrew/bin/diff"):
        DIFF_PROG = "/opt/homebrew/bin/diff"
        DIFF_FLAVOR = "gnu"
        DIFF_CMD = diff_cmd_gnu
    else:
        DIFF_PROG = "/usr/bin/diff"
        DIFF_FLAVOR = "bsd"
        DIFF_CMD = diff_cmd_bsd
else:
    DIFF_PROG = "diff"
    DIFF_FLAVOR = "gnu"
    DIFF_CMD = diff_cmd_gnu

DIFF_FENCES = DIFF_FLAVOR == "bsd"
