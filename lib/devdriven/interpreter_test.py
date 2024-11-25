import devdriven.interpreter as sut


def test_binary_op():
    assert sut.binary_op("==")(1, 1) is True
    assert sut.binary_op("=")(1, 1) is True
    assert sut.binary_op("==")(1, 2) is False
    assert sut.binary_op("!=")(1, 2) is True
    assert sut.binary_op("<")(1, 2) is True
    assert sut.binary_op(">")(1, 2) is False
    assert sut.binary_op("<=")(1, 1) is True
    assert sut.binary_op(">=")(2, 2) is True
    assert sut.binary_op("=~")("foo", "foo") is True
    assert sut.binary_op("=~")("foo", "bar") is False
    assert sut.binary_op("~=")("foo", "foo") is True
    assert sut.binary_op("~")("foo", "foo") is True
    assert sut.binary_op("NOPE") is None


def test_binary_op_const():
    assert sut.binary_op_const("==", 1)(1) is True
    assert sut.binary_op_const("=", 1)(1) is True
    assert sut.binary_op_const("==", 1)(2) is False
    assert sut.binary_op_const("!=", 1)(2) is True
    assert sut.binary_op_const("<", 1)(2) is False
    assert sut.binary_op_const(">", 1)(2) is True
    assert sut.binary_op_const("<=", 1)(1) is True
    assert sut.binary_op_const(">=", 2)(2) is True
    assert sut.binary_op_const("=~", "foo")("foo") is True
    assert sut.binary_op_const("=~", "foo")("bar") is False
    assert sut.binary_op_const("~=", "foo")("foo") is True


def test_unary_op():
    assert sut.unary_op("-")(2) == -2
    assert sut.unary_op("+")(3) == 3
    assert sut.unary_op("+")(-3) == -3
    assert sut.unary_op("not")(True) is False
    assert sut.unary_op("not")(False) is True
    assert sut.unary_op("not")(None) is True
    assert sut.unary_op("not")(5) is False
    assert sut.unary_op("not")("") is True
    assert sut.unary_op("abs")(-7) == 7
    assert sut.unary_op("NOPE") is None
