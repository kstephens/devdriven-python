import re
from typing import Any, Callable, Dict

Opts = Dict[str, Any]


class VariableError(Exception):
    pass


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def replace_vars(
    content: str,
    bindings: Opts,
    before: str = "${",
    after: str = "}",
    escape: str = "\\",
    blank_if_not_set: bool = False,
    keep_undefined: bool = False,
    convert: Callable | None = None,
):
    """
    Replace variables similarly to Bash:

    bindings = {"name": "value", "empty": ""}

    Basics:

    "${name}"                 == "value"
    "${name:?}"               == "value"
    "${name:?oh no!}"         == "value"
    "${name:-if-empty}"       == "value"
    "${name:+if-not-empty}"   == "if-not-empty"
    "${empty}"                == ""
    "${empty:?}"              !! "empty: not set"
    "${empty:?oh no!}"        !! "oh no!"
    "${empty:-if-empty}"      == "if-empty"
    "${empty:+if-not-empty}"  == ""
    "${name:=if-empty}"       == "value"
    "${undefined:=if-empty}"  == "if-empty" and env["undefined"] == "if-empty"
    "\\${name}"               == "${name}"

    # Extensions:

    "${name:<+before }"       == "before value"
    "${name:>+ after}"        == "value after"
    """
    convert = convert or (lambda _name, val: val)

    ref_rx = re.compile(
        r"(?P<ref>"
        f"(?P<escape>{re.escape(escape or '')})?"
        f"(?P<body>"
        f"{re.escape(before)}"
        r"(?P<name>[a-zA-Z][-_a-zA-Z0-9]*)"
        r"(?:(?P<modifier>:\?|:-|:\+|:=|:<\+|:>\+)"
        r"(?P<mod_val>.*?))?"
        f"{re.escape(after)}"
        r"))"
    )

    def replace(m):
        name, mod, mod_val = m["name"], m["modifier"], m["mod_val"]
        if escape and m["escape"]:
            return m["body"]
        if name not in bindings:
            if keep_undefined:
                return m["ref"]
            if blank_if_not_set:
                return ""
        val = convert(name, bindings.get(name))
        if val is None:
            val = ""
        else:
            val = str(val)
        if mod == ":?" and val == "":
            raise VariableError(mod_val or f"{name}: not set")
        if mod == ":-" and val == "":
            return mod_val
        if mod == ":+" and val != "":
            return mod_val
        if mod == ":=":
            if val == "":
                val = bindings[name] = mod_val
            return val
        if mod == ":<+" and val != "":
            return mod_val + val
        if mod == ":>+" and val != "":
            return val + mod_val
        return val

    return re.sub(ref_rx, replace, content)
