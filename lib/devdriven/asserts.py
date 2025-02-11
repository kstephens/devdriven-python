from typing import Any, Iterable, List, Callable, Tuple, TextIO
import os
import sys
from pathlib import Path
import hashlib
from pprint import pprint
from .file import file_md5

FilterFunc = Callable[[str], str]
Filepath = str
Command = str
FileOutputFunc = Callable[[Filepath], None]
ContextFunc = Callable[[str], str | None]
Difference = Tuple[int, str, str, str | None]
Differences = List[Difference]
Lines = List[str]


def assert_command_output(
    file: Filepath,
    command: Command,
    fix_line: FilterFunc | None = None,
    context_line: ContextFunc | None = None,
) -> Filepath:
    def run(actual_out: Filepath) -> None:
        system_command = f"exec 2>&1; set -x; {command} > {actual_out!r}"
        os.system(system_command)
        assert_log(f"assert_command_output : {command!r}")

    return assert_output(file, run, fix_line, context_line)


def assert_output_by_key(
    key: str,
    directory: Filepath,
    proc: FileOutputFunc,
    fix_line: FilterFunc | None = None,
    context_line: ContextFunc | None = None,
) -> Filepath:
    key_hash = hashlib.md5(key.encode("utf-8")).hexdigest()
    output_file = f"{directory}/{key_hash}"
    return assert_output(
        output_file,
        proc,
        fix_line=fix_line,
        context_line=context_line,
    )


def assert_output(
    file: Filepath,
    proc: FileOutputFunc,
    fix_line: FilterFunc | None = None,
    context_line: ContextFunc | None = None,
) -> Filepath:
    expect_out = f"{file}.out.expect"
    actual_out = f"{file}.out.actual"
    Path(expect_out).parent.mkdir(parents=True, exist_ok=True)
    proc(actual_out)
    return assert_files(
        actual_out, expect_out, fix_line=fix_line, context_line=context_line
    )


def assert_files(
    actual_out: Filepath,
    expect_out: Filepath,
    fix_line: FilterFunc | None = None,
    context_line: ContextFunc | None = None,
) -> str:
    if fix_line:
        fix_file(actual_out, fix_line)

    accept_actual = differences = None

    if os.path.isfile(expect_out):
        differences = compare_files(actual_out, expect_out, context_line=context_line)
        if differences:
            accept_actual = assertion_differences(actual_out, expect_out, differences)
    else:
        accept_actual = "Initialize"

    if accept_actual:
        assert_log(f"{accept_actual} : {expect_out!r} from {actual_out!r}")
        Path(actual_out).replace(expect_out)
        return expect_out
    if not differences:
        Path(actual_out).unlink(missing_ok=True)
        return expect_out
    return actual_out


def assertion_differences(
    actual_out: Filepath,
    expect_out: Filepath,
    differences: Differences,
):
    common_prefix = os.path.commonprefix([actual_out, expect_out])
    actual_suffix = actual_out.removeprefix(common_prefix)
    expect_suffix = expect_out.removeprefix(common_prefix)

    diff_command = f"diff --minimal -u {expect_out!r} {actual_out!r}"
    mv_command = f"mv {common_prefix}" + "{" + actual_suffix + "," + expect_suffix + "}"
    accept_command = "export ASSERT_DIFF_ACCEPT=1"

    assert_log(
        f"{common_prefix!r} : {len(differences)} differences found between {actual_suffix!r} and {expect_suffix!r}"
    )
    # for diff in differences:
    #    assert_log(f"{diff!r}")

    assert_log(f"To compare : {diff_command}")
    assert_log(f"To accept  : {mv_command}")
    assert_log(f"      OR   : {accept_command}")

    n_lines = 50
    assert_log(f"Difference: first {n_lines} lines")
    os.system(f"exec 2>&1; (set -x; {diff_command}) | head -{n_lines} 2>&1")

    if int(os.environ.get("ASSERT_DIFF_ACCEPT", "0")):
        accept_actual = "ASSERT_DIFF_ACCEPT"
    else:
        assert actual_out == expect_out
    return accept_actual


def compare_files(
    actual_out: Filepath,
    expect_out: Filepath,
    context_line: ContextFunc | None = None,
) -> Differences:
    with open(actual_out, "r", encoding="utf-8") as io:
        actual_lines = io.readlines()
    with open(expect_out, "r", encoding="utf-8") as io:
        expect_lines = io.readlines()

    actual_md5 = file_md5(actual_out)
    expect_md5 = file_md5(expect_out)

    if actual_md5 != expect_md5:
        assert_log(
            f"actual   : {actual_out!r} : {len(actual_lines)} lines : md5 {actual_md5!r}"
        )
        assert_log(
            f"expected : {expect_out!r} : {len(expect_lines)} lines : md5 {expect_md5!r}"
        )
    else:
        assert_log(
            f"SAME     : {actual_out!r} : {len(actual_lines)} lines : md5 {actual_md5!r}"
        )
    return compare_lines(actual_lines, expect_lines, context_line=context_line)


def compare_lines(
    actual_lines: Lines,
    expect_lines: Lines,
    context_line: ContextFunc | None = None,
) -> Differences:
    i = 0
    context = None
    differences = []
    for actual_line, expect_line in zip(actual_lines, expect_lines):
        actual_line, expect_line = actual_line[:-1], expect_line[:-1]
        i += 1
        if context_line:
            if new_context := context_line(actual_line):
                context = new_context
        if actual_line != expect_line:
            differences.append((i, actual_line, expect_line, context))
    return differences


def context_lines(
    side: str,
    lines: Lines,
    context_line: ContextFunc | None = None,
) -> List:
    if not context_line:
        return lines
    result, context = [], None
    for line in lines:
        if new_context := context_line(line):
            context = new_context
            result.append(f"### context: {side} {context}")
        result.append(line)
    return result


def fix_file(file: Filepath, fix_line: FilterFunc | None = None) -> None:
    # log(f'fix_file: {file!r}')
    file_tmp = f"{file}.tmp"
    with open(file_tmp, "w", encoding="utf-8") as tmp:
        with open(file, "r", encoding="utf-8") as out:
            while line := out.readline():
                if fix_line:
                    line = fix_line(line)
                tmp.write(line)
    # os.system(f'diff -U0 {file} {file_tmp}')
    os.rename(file_tmp, file)


def assert_log(msg: str | None = "") -> None:
    if msg:
        print(f"  ### assert : {msg}", file=sys.stderr)
    else:
        print("", file=sys.stderr)


######################################


Outputter = Callable[[TextIO], None]


def open_output(proc: Outputter) -> FileOutputFunc:
    def f(file: Filepath) -> None:
        with open(file, "w", encoding="utf-8") as output:
            proc(output)

    return f


def pp_output(data: Any) -> Outputter:
    def f(output: TextIO) -> None:
        pprint(data, stream=output, indent=2)

    return f


def lines_output(data: Any) -> Outputter:
    def make_line(row: Any) -> str:
        if isinstance(row, Iterable):
            return " ".join([str(x) for x in row])
        return str(row)

    def f(output: TextIO) -> None:
        for row in data:
            print(make_line(row), file=output)

    return f
