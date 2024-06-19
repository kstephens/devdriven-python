import tempfile
import devdriven.file as sut  # type: ignore

def test_read_file():
  assert len(sut.read_file('Makefile')) > 0
  assert len(sut.read_file('Makefile')) > 10
  assert isinstance(sut.read_file('Makefile'), bytes)
  assert isinstance(sut.read_file('Makefile', 'utf-8'), str)
  assert sut.read_file('Does-Not-Exist') is None

def test_file_size():
  assert sut.file_size('Makefile.common') > 99
  assert sut.file_size('Does-Not-Exist') is None

def test_file_md5():
  assert sut.file_md5('/dev/null') == 'd41d8cd98f00b204e9800998ecf8427e'
  assert sut.file_md5('Does-Not-Exist') is None

def test_file_nlines():
  def fut(buf, expected):
    with tempfile.NamedTemporaryFile() as tmp:
      tmp.write(buf)
      tmp.flush()
      actual = sut.file_nlines(tmp.name)
      tmp.close()
    assert (buf, actual) == (buf, expected)
  fut(b'', 0)
  fut(b'\n', 1)
  fut(b'\n\n', 2)
  fut(b'1', 1)
  fut(b'1\n', 1)
  fut(b'1\n2', 2)
  fut(b'1\n2\n', 2)
  fut(b'1\n2\n\3', 3)
  fut(b'1\n2\n\n', 3)
  fut(b'1\n2\n\n ', 4)
  assert sut.file_nlines('tests/devdriven/data/expected.txt') == 11
  assert sut.file_nlines('/dev/null') == 0
  assert sut.file_nlines('Does-Not-Exist') is None

def test_pickle_bz2():
  data = {'a': 1, 'b': 2}
  with tempfile.NamedTemporaryFile() as tmp:
    sut.pickle_bz2(tmp.name, 'wb', data)
    assert sut.pickle_bz2(tmp.name, 'rb') == data
