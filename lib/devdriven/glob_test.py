import re
import devdriven.glob as sut


def test_glob_to_regex():
    glob = "a/b"
    assert fut(glob, "") is False
    assert fut(glob, "a") is False
    assert fut(glob, "a/b") is True
    assert fut(glob, "a/bc") is False


def test_glob_star():
    glob = "*.c"
    assert fut(glob, "a.c") is True
    assert fut(glob, "b.b") is False
    assert fut(glob, "d/a.c") is False
    assert fut(glob, ".c") is False


def test_glob_star_star():
    glob = "**"
    assert fut(glob, "a.c") is True
    assert fut(glob, "d/a.c") is True
    assert fut(glob, "d/e/a.c") is True
    assert fut(glob, "d/e/b") is True
    glob = "**/*.c"
    assert fut(glob, "a.c") is False
    assert fut(glob, "d/a.c") is True
    assert fut(glob, "d/e/a.c") is True
    assert fut(glob, "d/e/b") is False
    glob = "/**"
    assert fut(glob, "a.c") is False
    assert fut(glob, "d/a.c") is False
    assert fut(glob, "/a.c") is True
    assert fut(glob, "/d/a.c") is True


def fut(glob, path):
    rx = sut.glob_to_regex(glob)
    # print('')
    # print(glob)
    # print(rx)
    return re.search(rx, path) is not None
