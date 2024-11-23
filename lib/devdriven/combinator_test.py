import re
import devdriven.combinator as sut

def test_constantly():
  assert sut.constantly(2)() == 2
  assert sut.constantly(3)(1) == 3
  assert sut.constantly(5)(a='1') == 5

def test_predicate():
  def f(x):
    return x + 1

  assert sut.predicate(f)(0) is True
  assert sut.predicate(f)(1) is True
  assert sut.predicate(f)(-1) is False

def test_negate():
  def f(x, y):
    return x == y

  assert sut.negate(f)(2, 2) is False
  assert sut.negate(f)(2, 3) is True

def test_bind_arg():
  assert sut.bind_arg(sut.identity, 0)(2, 3) == 2
  assert sut.bind_arg(sut.identity, 1)(2, 3) == 3
  assert sut.bind_arg(sut.identity, -1)(2, 3) == 3

def test_bind_args():
  def return_args(*args):
    return list(args)

  def t(idxs):
    g = sut.bind_args(return_args, idxs)
    return g(2, 3, 5)

  assert t([]) == []
  assert t([0]) == [2]
  assert t([1, 0]) == [3, 2]

def test_and_comp():
  def f(x):
    return x

  def g(_x):
    return 'g'

  assert sut.and_comp(f, g)(False) is False
  assert sut.and_comp(f, g)('') == ''
  assert sut.and_comp(f, g)(True) == 'g'

def test_or_comp():
  def f(x):
    return x

  def g(_x):
    return 'g'

  assert sut.or_comp(f, g)(False) == 'g'
  assert sut.or_comp(f, g)('') == 'g'
  assert sut.or_comp(f, g)(True) is True
  assert sut.or_comp(f, g)(0) == 'g'
  assert sut.or_comp(f, g)(1) == 1

def test_if_comp():
  def f(x):
    return x

  def g(_x):
    return 'g'

  def h(_x):
    return 'h'

  assert sut.if_comp(f, g, h)(True) == 'g'
  assert sut.if_comp(f, g, h)(False) == 'h'

def test_is_none():
  def f(x):
    return x

  assert sut.is_none(f)(None) is True
  assert sut.is_none(f)(True) is False
  assert sut.is_none(f)(False) is False
  assert sut.is_none(f)('') is False

def test_is_not_none():
  def f(x):
    return x

  assert sut.is_not_none(f)(None) is False
  assert sut.is_not_none(f)(True) is True
  assert sut.is_not_none(f)(False) is True
  assert sut.is_not_none(f)('') is True

def test_compose():

  def f(x, y):
    return x + y

  def g(z):
    return z * 2

  def h(z):
    return z * 3 + 5

  assert sut.compose(f)(2, 3) == 5
  assert sut.compose(g, f)(5, 7) == 24
  assert sut.compose(sut.identity, g, f)(5, 7) == 24
  assert sut.compose(h, g, f)(11, 13) == 149

def test_re_pred():
  assert sut.re_pred(re.compile("ab"))("abc") is True
  assert sut.re_pred("ab")("abc") is True
  assert sut.re_pred("ab")("bc") is False
  assert sut.re_pred("bc")("abc") is True
  assert sut.re_pred(12)("123") is True
  assert sut.re_pred(12)(123) is True
