import time

import pytest

from .timeout import with_timeout


def test_with_timeout():
    def fn(sec):
        time.sleep(sec)
        return 2

    assert with_timeout(fn, 0.10)(0.01) == 2
    assert with_timeout(fn, 0.10)(0.01) == 2

    with pytest.raises(TimeoutError):
        with_timeout(fn, 0.10)(0.5)
