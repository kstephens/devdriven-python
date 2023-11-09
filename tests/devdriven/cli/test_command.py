from devdriven.cli import Command
import shlex

def test_parse_argv():
  examples = [
    ('', [], {}),
    ('a', ['a'], {}),
    ('a -after', ['a', '-after'], {}),
    ('-a', [], {'a': True}),
    ('--ab c d', ['c', 'd'], {'ab': True}),
    ('++ab c d', ['c', 'd'], {'ab': False}),
    ('--ab=foo c d', ['c', 'd'], {'ab': 'foo'}),
    ('-- --ab=foo c d', ['--ab=foo', 'c', 'd'], {}),
    ('-fg --fg +jk', [], {'foo': True, 'g': True, 'fg': True, 'j': False, 'k': False}),
  ]
  for cmdline, expected_args, expected_opts in examples:
    c = Command()
    c.opt_char_map = { 'f': 'foo' }
    argv = shlex.split(cmdline)
    c.parse_argv(argv)
    assert c.args == expected_args
    assert c.opts == expected_opts
