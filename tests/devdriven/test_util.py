import subprocess
from devdriven import util

def test_maybe_decode_bytes():
    assert util.maybe_decode_bytes(b'A') == 'A'
    assert util.maybe_decode_bytes(b'\xff') is None
    assert util.maybe_decode_bytes(None) is None

def test_exec_command():
    result = util.exec_command(['echo', 'OK'])
    assert result.returncode == 0
    assert result.stdout is None
    assert result.stderr is None

    result = util.exec_command(['echo', 'OK'],
                               capture_output=True)
    assert result.returncode == 0
    assert result.stdout == b'OK\n'
    assert result.stderr == b''

    result = util.exec_command(['echo ERROR >&2'],
                               capture_output=True, shell=True)
    assert result.returncode == 0
    assert result.stdout == b''
    assert result.stderr == b'ERROR\n'

    ex = None
    try:
        util.exec_command(['false'], check=True)
    except subprocess.CalledProcessError as err:
        ex = err
    assert ex is not None

def test_read_file():
    assert len(util.read_file('Makefile')) > 0
    assert len(util.read_file('Makefile', default=b'DEFAULT')) > 10
    assert len(util.read_file('UNKNOWN-FILE', default=b'DEFAULT')) == 7

def test_file_size():
    assert util.file_size('Makefile') > 99
    assert util.file_size('Makefile', default=7) > 7
    assert util.file_size('UNKNOWN-FILE') is None
    assert util.file_size('UNKNOWN-FILE', default=7) == 7

def test_partition():
    assert util.partition(['a', 1, 'b', 2], lambda e: isinstance(e, str)) == (['a', 'b'], [1, 2])

def test_frequency():
    assert util.frequency(['a', 1, 'a', 2]) == {'a': 2, 1: 1, 2: 1}

def test_uniq_by():
    assert util.uniq_by([['a', 1], ['b', 2], ['a', 2]], key=lambda e: e[0]) == [['a', 1], ['b', 2]]

def test_parse_commands():
    assert not util.parse_commands([])
    assert util.parse_commands(['cmd1']) == \
        [['cmd1']]
    assert util.parse_commands(['cmd1', 'a']) == \
        [['cmd1', 'a']]
    assert util.parse_commands(['cmd1', 'a', 'b', ',', 'cmd2', 'c']) == \
        [['cmd1', 'a', 'b'], ['cmd2', 'c']]

def test_file_md5():
    assert util.file_md5('/dev/null') == 'd41d8cd98f00b204e9800998ecf8427e'
    assert util.file_md5('Does-Not-Exist') is None

def test_file_nlines():
    assert util.file_nlines('tests/data/expected.txt', default=2) == 11
    assert util.file_nlines('/dev/null', default=3) == 0
    assert util.file_nlines('Does-Not-Exist', default=5) == 5
    assert util.file_nlines('Does-Not-Exist') is None

def test_elapsed_ms():
    result, dt_ms = util.elapsed_ms(lambda x, y: 1 + x + y, 2, y=3)
    assert result == 6
    assert dt_ms > 0

def test_diff_files():
    assert util.file_nlines('tests/data/expected.txt') == 11
    assert util.file_nlines('tests/data/actual.txt') == 10

    result = util.diff_files('tests/data/expected.txt', 'tests/data/actual.txt')
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

    result = util.diff_files('tests/data/expected.txt', 'tests/data/expected.txt')
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

    result = util.diff_files('tests/data/expected.txt', 'Does-Not-Exist.txt')
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
    result = util.diff_files_stats(*args)
    # print(f'{repr(args)} -> {repr(result)}')
    return result
