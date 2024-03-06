import devdriven.combinator as sut

def test_constantly():
  assert sut.constantly(2)() == 2
  assert sut.constantly(3)(1) == 3
  assert sut.constantly(5)(a='1') == 5

def test_negate():
  def f(x, y):
    return x == y
  assert sut.negate(f)(2, 2) is False
  assert sut.negate(f)(2, 3) is True

def test_compose():

  def f(x, y):
    return x + y

  def g(z):
    return z * 2

  def h(z):
    return z * 3 + 5

  def identity(z):
    return z

  assert sut.compose(f)(2, 3) == 5
  assert sut.compose(g, f)(5, 7) == 24
  assert sut.compose(identity, g, f)(5, 7) == 24
  assert sut.compose(h, g, f)(11, 13) == 149
