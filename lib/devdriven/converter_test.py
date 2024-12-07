import pandas as pd
from . import converter as sut


def make_dataframe():
    df = pd.DataFrame({"c1": ["a", "b"], "c2": [3, 5]})
    return df


def test_init():
    obj = make()
    assert obj.encoding == "utf-8"
    assert obj.record_separator == "\n"
    assert obj.rich_format == "json"


def test_as_bytes():
    obj = make()
    fut = obj.as_bytes
    assert fut(b"123") == b"123"
    assert fut("abc") == b"abc"
    assert fut(567) == b"567"
    assert fut([9, 10]) == b"[\n  9,\n  10\n]"


def test_as_str():
    obj = make()
    fut = obj.as_str
    assert fut(b"123") == "123"
    assert fut("abc") == "abc"
    assert fut(567) == "567"
    assert fut([9, 10]) == "[\n  9,\n  10\n]"


def test_as_iterable():
    obj = make()
    # dis.dis(obj.as_iterable); jkasdjfsd

    def fut(data, elem_type="str"):
        result = obj.as_iterable(data, elem_type)
        # print(repr(fut([9, 10])))
        # ic(fut([9, 10])); asdfsdf
        return result

    assert fut(b"123") == ["123"]
    assert fut("abc") == ["abc"]
    assert fut(567) == ["567"]
    assert fut(567.10) == ["567.1"]
    assert fut(567, "bytes") == [b"567"]
    assert fut([9, 10]) == ["9", "10"]
    assert list(fut("abc\ndef\n")) == ["abc\n", "def\n"]
    assert list(fut("abc\ndef\n", "bytes")) == [b"abc\n", b"def\n"]
    assert list(fut(b"abc\ndef\n")) == ["abc\n", "def\n"]
    assert list(fut(b"abc\ndef\n", "bytes")) == [b"abc\n", b"def\n"]
    assert list(fut(["a"])) == ["a"]
    assert list(fut([2, "3", 5], None)) == [2, "3", 5]
    assert list(fut((2, "3", 5), None)) == [2, "3", 5]
    assert list(fut({2: "3", 5: 7}, None)) == [[2, "3"], [5, 7]]
    assert list(fut([2, "3", 5])) == ["2", "3", "5"]
    assert list(fut({2: "3", 5: 7})) == ['[\n  2,\n  "3"\n]', "[\n  5,\n  7\n]"]
    assert list(fut((2, "3", 5))) == ["2", "3", "5"]
    # assert list(fut()


def x_test_as_str():
    obj = make()
    fut = obj.as_str
    assert fut(b"123") == "123"
    assert fut("abc") == "abc"
    assert fut(567) == "567"
    assert fut([9, 10]) == "[\n  9,\n  10\n]"


def test_as_dict():
    obj = make()
    fut = obj.as_dict
    assert fut({}) == {}
    assert fut({"a": 1}) == {"a": 1}
    assert fut({"123": 1}, "int", "float") == {123: 1.0}


def test_as_rich_format_json():
    obj = make(rich_format=sut.JSON)
    fut = obj.as_rich
    # assert fut(b'123') == '123'
    assert fut("abc") == '"abc"'
    assert fut(567) == "567"
    assert fut(True) == "true"
    assert fut("true") == '"true"'
    assert fut(False) == "false"
    assert fut("false") == '"false"'
    assert fut(None) == "null"
    assert fut([9, 10]) == "[\n  9,\n  10\n]"
    assert fut({2: 3, 5: 7}) == '{\n  "2": 3,\n  "5": 7\n}'
    assert fut((13, 17)) == "[\n  13,\n  17\n]"


def test_as_rich_format_yaml():
    obj = make(rich_format=sut.YAML)
    fut = obj.as_rich
    # assert fut(b'123') == '123'
    assert fut("abc") == "abc\n...\n"
    assert fut(567) == "567\n...\n"
    assert fut(True) == "true\n...\n"
    assert fut("true") == "'true'\n"
    assert fut(False) == "false\n...\n"
    assert fut("false") == "'false'\n"
    assert fut(None) == "null\n...\n"
    assert fut([9, 10]) == "- 9\n- 10\n"
    assert fut({2: 3, 5: 7}) == "2: 3\n5: 7\n"
    assert fut((13, 17)) == "!!python/tuple\n- 13\n- 17\n"


def make(**kwargs):
    return sut.Converter(**kwargs)
