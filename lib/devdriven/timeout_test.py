import time

import pytest

from .timeout import with_timeout


def test_with_timeout():
    def fn(sec):
        time.sleep(sec)
        return 2

    assert with_timeout(0.0, fn)(0.25) == 2
    assert with_timeout(0.5, fn)(0.25) == 2

    with pytest.raises(TimeoutError):
        with_timeout(0.5, fn)(0.75)
