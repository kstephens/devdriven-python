import tempfile
from random import randint
from pathlib import Path
import devdriven.cache as sut  # type: ignore
# from icecream import ic

def test_PickleCache():
  # ic.configureOutput(includeContext=True, contextAbsPath=True)
  with tempfile.NamedTemporaryFile() as tmp:
    path = Path(tmp.name)
    data = [randint(10, 100) for _i in range(10)]
    def return_data():
      return data

    cache = sut.PickleCache(path, return_data)
    cache.flush()
    assert cache.ready is False
    assert cache.data is data
    assert cache.ready is True
    assert path.stat().st_size > 0
    assert cache.data is data

    def return_fail():
      raise Exception('return_fail')

    cache = sut.PickleCache(path, return_fail)
    assert cache.ready is False
    assert path.stat().st_size > 0
    assert cache.data == data
