import re
import pytest


def func_doc_example_test(func):
    """
    Extract func.__doc__ test cases and assert them.
    """
    func_name = func.__name__
    examples = func.__doc__

    test_cases = [line.strip() for line in examples.splitlines()]
    test_cases = list(
        map(lambda line: re.match(r'^ *(\S+) +(==|!=|!!) +(.*)', line), test_cases)
    )
    test_cases = [(m[1], m[2], m[3]) for m in test_cases if m]

    for args, op, expected in test_cases:
        call_desc = f"{func_name}({args})"
        if op == "!!":
            assert_expr = f"""
with pytest.raises({expected}):
    {call_desc}
"""
        else:
            assert_expr = f"assert {call_desc} {op} {expected!r}"
        print(assert_expr)
        exec(assert_expr)
