from devdriven import diff

def test_diff_files():
  assert diff.file_nlines('tests/devdriven/data/expected.txt') == 11
  assert diff.file_nlines('tests/devdriven/data/actual.txt') == 10

  result = diff.diff_files('tests/devdriven/data/expected.txt', 'tests/devdriven/data/actual.txt')
  expected = {
    "correct": False,
    "expected": 11,
    "actual": 10,
    "old": 4,
    "new": 3,
    "differences": 7,
    "correct_ratio": 0.6666666666666666,
    "correct_percent": 66.67,
    "exit_code": 1
  }
  assert result == expected

  result = diff.diff_files('tests/devdriven/data/expected.txt', 'tests/devdriven/data/expected.txt')
  expected = {
    "correct": True,
    "expected": 11,
    "actual": 11,
    "old": 0,
    "new": 0,
    "differences": 0,
    "correct_ratio": 1.0,
    "correct_percent": 100.0,
    "exit_code": 0
  }
  assert result == expected

def test_diff_files_non_existant():
  result = diff.diff_files('tests/devdriven/data/expected.txt', 'Does-Not-Exist.txt')
  expected = {
    "correct": False,
    "expected": 11,
    "actual": None,
    "old": None,
    "new": None,
    "differences": None,
    "correct_ratio": 0.0,
    "correct_percent": 0.0,
    "exit_code": 2
  }
  assert result == expected

  result = diff.diff_files('Does-Not-Exist.txt', 'tests/devdriven/data/expected.txt')
  expected = {
    'actual': 11,
    'correct': False,
    'correct_percent': 0.0,
    'correct_ratio': 0.0,
    'differences': None,
    'exit_code': 2,
    'expected': None,
    'new': None,
    'old': None,
  }
  assert result == expected

  result = diff.diff_files('Does-Not-Exist.txt', 'Does-Not-Exist.txt')
  expected = {
    'actual': None,
    'correct': False,
    'correct_percent': 0.0,
    'correct_ratio': 0.0,
    'differences': None,
    'exit_code': 2,
    'expected': None,
    'new': None,
    'old': None,
  }
  assert result == expected

def test_diff_files_stats():
  assert diff_files_stats(0, 0, 0, 0, 0) == \
    {'correct': True, 'expected': 0, 'actual': 0,
     'old': 0, 'new': 0, 'differences': 0,
     'correct_ratio': 1.0, 'correct_percent': 100.0, 'exit_code': 0}
  assert diff_files_stats(10, 10, 0, 0, 0) == \
    {'correct': True, 'expected': 10, 'actual': 10,
     'old': 0, 'new': 0, 'differences': 0,
     'correct_ratio': 1.0, 'correct_percent': 100.0, 'exit_code': 0}
  assert diff_files_stats(10, 9, 1, 0, 1) == \
    {'correct': False, 'expected': 10, 'actual': 9,
     'old': 1, 'new': 0, 'differences': 1,
     'correct_ratio': 0.9473684210526315, 'correct_percent': 94.74, 'exit_code': 1}
  assert diff_files_stats(9, 10, 0, 1, 1) == \
    {'correct': False, 'expected': 9, 'actual': 10,
     'old': 0, 'new': 1, 'differences': 1,
     'correct_ratio': 0.9473684210526315, 'correct_percent': 94.74, 'exit_code': 1}
  assert diff_files_stats(10, 9, 1, 0, 1) == \
    {'correct': False, 'expected': 10, 'actual': 9,
     'old': 1, 'new': 0, 'differences': 1,
     'correct_ratio': 0.9473684210526315, 'correct_percent': 94.74, 'exit_code': 1}
  assert diff_files_stats(10, 11, 0, 1, 1) == \
    {'correct': False, 'expected': 10, 'actual': 11,
     'old': 0, 'new': 1, 'differences': 1,
     'correct_ratio': 0.9523809523809523, 'correct_percent': 95.24, 'exit_code': 1}
  assert diff_files_stats(10, 10, 1, 1, 1) == \
    {'correct': False, 'expected': 10, 'actual': 10,
     'old': 1, 'new': 1, 'differences': 2,
     'correct_ratio': 0.9, 'correct_percent': 90.0, 'exit_code': 1}
  assert diff_files_stats(0, 10, 0, 10, 0) == \
    {'correct': False, 'expected': 0, 'actual': 10,
     'old': 0, 'new': 10, 'differences': 10,
     'correct_ratio': 0.0, 'correct_percent': 0.0, 'exit_code': 0}

def diff_files_stats(*args):
  result = diff.diff_files_stats(*args)
  # print(f'{repr(args)} -> {repr(result)}')
  return result
