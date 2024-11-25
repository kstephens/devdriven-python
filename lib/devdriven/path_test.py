from .path import clean_path


def test_clean_path():
    assert clean_path(".a") == ".a"
    assert clean_path("/.a") == "/.a"
    assert clean_path(".") == "."
    assert clean_path("./") == ""  # ???
    assert clean_path("..") == ""
    assert clean_path("../") == ""  # ???
    assert clean_path("/..") == "/"
    assert clean_path("/../a") == "/a"
    assert clean_path("a") == "a"
    assert clean_path("/a") == "/a"
    assert clean_path("//a") == "/a"
    assert clean_path("//a//") == "/a/"
    assert clean_path("dir//a//") == "dir/a/"
    assert clean_path("/root//a//") == "/root/a/"
    assert clean_path("dir/../a/b") == "a/b"
    assert clean_path("/root/../b") == "/b"
    assert clean_path("dir/a/../b") == "dir/b"
    assert clean_path("dir/a/../../b/c") == "b/c"
