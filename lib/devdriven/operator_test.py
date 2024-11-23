from typing import Callable
import pytest
import devdriven.operator as sut

def test_bop():
  def bop(name: str) -> Callable:
    f = sut.binary_op(name)
    assert f is not None
    return sut.binary_coerce(f, sut.COERCE_BINARY_RIGHT_NATURAL)

  assert pytest.approx(bop('+')(2.3, "5.7")) == 8.0
  assert pytest.approx(sut.left_comp(bop('+'), bop('*'))(2.3, 5.7, "11.13"), 0.01) == 65.74
