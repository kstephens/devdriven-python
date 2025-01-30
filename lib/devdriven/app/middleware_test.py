from io import StringIO
from pprint import pprint
import re
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


def test_capture_exception():
    def failing_app(_req):
        raise ValueError("test_capture_exception")

    app = failing_app
    app = sut.capture_exception(app, status=599, with_backtrace=True)
    request = {}
    status, headers, body = app(request)
    exc = request["exception"]
    assert repr(exc) == "ValueError('test_capture_exception')"
    assert status == 599
    assert headers["Content-Type"] == "text/plain"
    assert body[0] == f"ERROR: {exc!r}\n"
    assert re.search(r"middleware.py: \d+\n$", body[1])
    assert re.search(f"{__file__}: \\d+\n$", body[2])
