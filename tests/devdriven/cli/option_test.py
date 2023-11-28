from devdriven.cli.option import Option
from dataclasses import dataclass, asdict
from icecream import ic

def test_parse_doc_long_flag():
  o = Option().parse_doc('--opt  |  desc.')
  assert asdict(o) == {
    'aliases': [],
                'arg': '--opt',
                'default': None,
                'description': 'desc.',
                'full': '--opt',
                'kind': 'flag',
                'name': 'opt',
                'style': 'doc',
                'value': True}

def test_parse_doc_long_flag_default():
  o = Option().parse_doc('--opt  |  desc.  Default: True.')
  assert asdict(o) == {
    'aliases': [],
                'arg': '--opt',
                'default': "True",
                'description': 'desc.  Default: True.',
                'full': '--opt',
                'kind': 'flag',
                'name': 'opt',
                'style': 'doc',
                'value': True}

def test_parse_doc_long_flag_false():
  o = Option().parse_doc('++opt  |  desc.')
  assert asdict(o) == {
    'aliases': [],
                'arg': '++opt',
                'default': None,
                'description': 'desc.',
                'full': '--opt',
                'kind': 'flag',
                'name': 'opt',
                'style': 'doc',
                'value': False}

def test_parse_doc_alias_flag():
  o = Option().parse_doc('--opt, -o  |  opt: doc')
  assert asdict(o) == {
    'aliases': [{'aliases': [],
                             'arg': '-o',
                             'default': None,
                             'description': 'opt: doc',
                             'full': '-o',
                             'kind': 'flag',
                             'name': 'o',
                             'style': 'doc',
                             'value': True}],
                'arg': '--opt',
                'default': None,
                'description': 'opt: doc',
                'full': '--opt',
                'kind': 'flag',
                'name': 'opt',
                'style': 'doc',
                'value': True}

def test_parse_doc_long_opt():
  o = Option().parse_doc('--opt  |  desc.')
  assert asdict(o) == {
    'aliases': [],
                'arg': '--opt',
                'default': None,
                'description': 'desc.',
                'full': '--opt',
                'kind': 'flag',
                'name': 'opt',
                'style': 'doc',
                'value': True}

def test_parse_doc_long_opt_default():
  o = Option().parse_doc('--opt  |  desc.  Default: True.')
  assert asdict(o) == {
    'aliases': [],
                'arg': '--opt',
                'default': "True",
                'description': 'desc.  Default: True.',
                'full': '--opt',
                'kind': 'flag',
                'name': 'opt',
                'style': 'doc',
                'value': True}


def test_parse_doc_long_opt_false():
  o = Option().parse_doc('++opt  |  desc.')
  assert asdict(o) == {
    'aliases': [],
                'arg': '++opt',
                'default': None,
                'description': 'desc.',
                'full': '--opt',
                'kind': 'flag',
                'name': 'opt',
                'style': 'doc',
                'value': False}

def test_parse_doc_alias_opt():
  o = Option().parse_doc('--opt, -o  |  opt: doc')
  assert asdict(o) == {
    'aliases': [{'aliases': [],
                             'arg': '-o',
                             'default': None,
                             'description': 'opt: doc',
                             'full': '-o',
                             'kind': 'flag',
                             'name': 'o',
                             'style': 'doc',
                             'value': True}],
                'arg': '--opt',
                'default': None,
                'description': 'opt: doc',
                'full': '--opt',
                'kind': 'flag',
                'name': 'opt',
                'style': 'doc',
                'value': True}
