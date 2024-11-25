from . import Options


def test_parse_argv():
    argv = ["-abc", "--flag", "--opt=g", "h", "i", "-j"]
    obj = Options()
    obj.parse_argv(argv.copy())
    assert obj.argv == argv
    assert list(map(lambda o: o.name, obj.opts)) == ["a", "b", "c", "flag", "opt"]
    assert list(map(lambda o: o.value, obj.opts)) == [True, True, True, True, "g"]
    assert obj.args == ["h", "i", "-j"]


def test_parse_argv_dash():
    argv = ["-abc", "--flag", "--", "--opt=g", "h", "i", "-j"]
    obj = Options()
    obj.parse_argv(argv.copy())
    assert obj.argv == argv
    assert obj.opt("a") is True
    assert obj.opt("a", 2) is True
    assert obj.opt("b", 3) is True
    assert obj.opt("c", 5) is True
    assert obj.opt("flag", 7) is True
    assert list(map(lambda o: o.name, obj.opts)) == ["a", "b", "c", "flag"]
    assert list(map(lambda o: o.value, obj.opts)) == [
        True,
        True,
        True,
        True,
    ]
    assert obj.args == ["--opt=g", "h", "i", "-j"]


def test_parse_argv_dash_in_args():
    argv = ["-abc", "--flag", "--opt=g", "h", "i", "-j"]
    obj = Options()
    obj.parse_argv(argv.copy())
    assert obj.args == ["h", "i", "-j"]
    assert obj.opt("a", 2) is True
    assert obj.opt("b", 3) is True
    assert obj.opt("c", 3) is True
    assert obj.opt("opt", 5) == "g"
    assert obj.opt("x", 7) == 7
    assert obj.opt("j", 11) == 11
