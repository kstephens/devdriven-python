from io import StringIO
from pprint import pprint
from . import middleware as sut

# from icecream import ic


def something_useful_app(req: sut.Req) -> sut.Res:
    x, y = req["input.data"]
    return 200, {}, (x * y,)


def test_full_stack():
    app = something_useful_app
    app = sut.trace(app)
    app = sut.decode_json(app)
    # stack = sut.capture_exception(stack, with_traceback=True)
    app = sut.encode_json(app, indent=2)
    app = sut.content_length(app)
    app = sut.http_response(app)
    app = sut.write_output(app)
    app = sut.trace(app)
    app = sut.read_input(app)

    input_stream = StringIO('["ab", 5]')
    output_stream = StringIO("")
    req = {
        "input.stream": input_stream,
        "output.stream": output_stream,
        "Content-Type": "application/json",
    }
    actual = app(req)
    pprint(actual)
    expected = (
        200,
        {"Content-Length": 13, "Content-Type": "application/json"},
        [
            "HTTP/1.1 200 OK\n",
            "Content-Type: application/json\n",
            "Content-Length: 13\n",
            "\n",
            '"ababababab"\n',
        ],
    )
    assert actual == expected

    assert req.get("output.stream") is None
    actual = output_stream.getvalue()
    expected = """HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 13

"ababababab"
"""
    print(actual)
    # pprint(actual)
    assert actual == expected


def test_yaml_coder():
    app = something_useful_app
    app = sut.decode_yaml(app)
    app = sut.encode_yaml(app)
    app = sut.http_response(app)
    app = sut.write_output(app)
    app = sut.read_input(app)

    output_stream = StringIO("")
    input_stream = StringIO(
        """
- ab
- 5
"""
    )
    req = {
        "input.stream": input_stream,
        "output.stream": output_stream,
        "Content-Type": "application/yaml",
    }
    app(req)
    actual = output_stream.getvalue()
    expected = """HTTP/1.1 200 OK
Content-Type: application/yaml
Content-Length: 15

ababababab
...
"""
    print(actual)
    # pprint(actual)
    assert actual == expected
