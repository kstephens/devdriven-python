import re

import pytest

from .replace_vars import VariableError, replace_vars


def test_replace_vars():
    test_cases = replace_vars.__doc__.splitlines()
    test_cases = list(
        map(lambda line: re.match(r'^ *"([^"]+)" +(==) +"([^"]*)"', line), test_cases)
    )
    test_cases = [(m[1], m[2], m[3]) for m in test_cases if m]

    bindings = {"name": "value", "empty": ""}

    for content, op, expected in test_cases:
        assert replace_vars(content, bindings) == expected, (
            f"{content!r} {op} {expected!r}"
        )
    assert bindings["undefined"] == "if-empty"

    with pytest.raises(VariableError, match="empty: not set"):
        replace_vars("${empty:?}", bindings)

    with pytest.raises(VariableError, match="oh no!"):
        replace_vars("${empty:?oh no!}", bindings)

    assert replace_vars("${keep:?}", bindings, keep_undefined=True) == "${keep:?}"

    def blank_if_not_set(content):
        return replace_vars(content, bindings, blank_if_not_set=True)

    assert blank_if_not_set("${not-set:?}") == ""
    assert blank_if_not_set("${name:+not-blank}") == "not-blank"
    assert blank_if_not_set("${empty:+not-blank}") == ""
    assert blank_if_not_set("${not-set:+not-blank}") == ""
    assert blank_if_not_set("${name:-not-blank}") == "value"
    assert blank_if_not_set("${empty:-is-blank}") == "is-blank"
    assert blank_if_not_set("${not-set:-is-blank}") == ""
