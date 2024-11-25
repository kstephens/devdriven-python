from typing import List, Dict
import logging
import shlex
import re

Command = List[str]


class MacroExpander:
    def __init__(self, macros: Dict[str, str], max_expansions: int = 16):
        self.macros = macros
        self.max_expansions = max_expansions

    def expand(self, command: Command) -> Command:
        prev = curr = command
        for _i in range(self.max_expansions):
            prev = curr
            curr = self.expand_macro(prev)
            if prev == curr or prev[0] == curr[0]:
                return curr
        logging.warning(
            "config : command : expanded %d times %s ", self.max_expansions, command
        )
        return curr

    def expand_macro(self, command: Command) -> Command:
        name, *argv = command
        if macro := self.macros.get(name):

            def expand(m: re.Match) -> str:
                if indx := m["indx"]:
                    return get_safe(command, int(indx))
                if m["glob"] or m["args"]:
                    return " ".join(argv)
                if indx := m["indx_q"]:
                    return shlex.join([get_safe(command, int(indx))])
                if m["glob_q"]:
                    arg = m["glob_q_pre"] + " ".join(argv) + m["glob_q_post"]
                    return shlex.join([arg])
                if m["args_q"]:
                    args = [m["args_q_pre"] + arg + m["args_q_post"] for arg in argv]
                    return shlex.join(args)
                assert not "here"
                return "<<INVALID>>"

            exp = re.sub(MACRO_REFERERENCE_RX, expand, macro)
            return shlex.split(exp)
        return command


def arg_rx(name, pat):
    return f'(?:"(?P<{name}_q_pre>[^$]*)\\$(?P<{name}_q>{pat})(?P<{name}_q_post>[^"]*)")|\\$(?P<{name}>{pat})'


MACRO_REFERERENCE_RX = re.compile(
    "|".join(
        [
            arg_rx("indx", r"-?\d+"),
            arg_rx("glob", r"[*]"),
            arg_rx("args", r"[@]"),
        ]
    )
)


def get_safe(a: List[str], i: int) -> str:
    try:
        return a[i]
    except IndexError:
        return ""
