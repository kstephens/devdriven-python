"""
Application middleware combinators inspired Python WSGI and Ruby Rack.

An "App" is anything callable with a single dict argument:
It receives a "Request": typically a Dict of input: headers, body and customer values passed along an "application stack".
It returns a "Response": Tuple of HTTP status code, headers and a body (sequence of response chunks).
Both applications and middleware follow the same protocol.
Combinators create new Apps by wrapping others.

Input combinators follow this pattern:

def compose_input_handler(app: App) -> App:
    def input_handler(req: Req) -> Res:
        do_something_with_input(req)
        return app(req)

Output combinators follow this pattern:

def compose_output_handle(app: App):
    def output_handler(req: Req) -> Res:
            status, headers, body = app(req)
            # alter status, header, body in some manner.
            return status, headers, body
        return status, headers,

"""

from typing import Any, Dict, Tuple, Iterable, Callable
import json
import re
import sys
from pprint import pprint
from http.client import responses as response_names

Status = int
Headers = Dict[str, Any]
Body = Iterable
Res = Tuple[Status, Headers, Body]
Req = Dict[str, Any]
App = Callable[[Req], Res]


def is_success(status: Status) -> bool:
    return status in range(200, 300)


def capture_exception(app: App, status=500, cls=Exception) -> App:
    "Captures any exception and creates a text/plain error document."

    def capturer(req: Req) -> Res:
        try:
            return app(req)
        # pylint: disable-next=broad-exception-caught
        except cls as exc:
            return status, {"Content-Type": "text/plain"}, [f"ERROR: {exc}"]

    return capturer


def default(app: App, defaults: Req) -> App:
    "Defaults any req values that are not defined."

    def defaulter(req: Req):
        for k, v in defaults.items():
            if k not in req:
                req[k] = v
        return app(req)

    return defaulter


def override(app: App, overrides: Req) -> App:
    "Overrides req values."

    def overrider(req: Req):
        req.update(overrides)
        return app(req)

    return overrider


def read_input(app: App, read: Callable[[Any], str]) -> App:
    "Reads body.stream"

    def reader(req: Req) -> Res:
        req["input.content"] = read(req)
        return app(req)

    return reader


def read_wsgi(app: App) -> App:
    return read_input(app, lambda req: req["wsgi.input"].read())


Coder = Callable[[Any], Any]
Encoder = Callable[[Any], str]
Decoder = Callable[[str], Any]


def decode(app: App, coder: Decoder, expected_types=None, strict=False) -> App:
    """
    Decodes body with coder(bytes) for expected_types.
    If strict and Content-Type is not expected, return 400.
    """

    def decoder(req: Req) -> Res:
        if "input.data" not in req:
            req["input.data"] = coder("input.content")
            content_type = req.get("Content-Type")
            if strict and expected_types and content_type not in expected_types:
                msg = f"expected Content-Type: {expected_types!r} : given {content_type!r}"
                return 400, {}, (msg,)
        return app(req)

    return decoder


def encode(app: App, coder: Encoder, content_type="text/plain") -> App:
    """
    Encodes body with coder(body[0]).
    Body *must* contain only one element.
    """

    def encoder(req: Req) -> Res:
        status, headers, body = app(req)
        content = "".join(map(coder, body))
        headers |= {
            "Content-Type": content_type,
            "Content-Length": len(content),
        }
        return status, headers, (content,)

    return encoder


def decode_json(app: App, **kwargs) -> App:
    "Decodes JSON content."

    def decoder(data: str) -> Any:
        return json.loads(data, **kwargs)

    return decode(app, decoder)


def encode_json(app: App, **kwargs) -> App:
    "Encodes data as JSON."

    def encoder(data: Any) -> str:
        return json.dumps(data, **kwargs) + "\n"

    return encode(app, encoder)


def write_body(app: App, output=sys.stdout) -> App:
    "Writes body elements to output."

    def writer(req) -> Res:
        status, _, body = app(req)
        for block in body:
            output.write(block)
        return status, _, []

    return writer


def trace(app: App, prefix="") -> App:
    "Traces requests and responses."

    def tracer(req):
        print(f"  ### {prefix} REQ ################################")
        pprint(req)
        print(f"  ### {prefix} BEG ################################")
        result = app(req)
        print(f"  ### {prefix} END ################################")
        pprint(result)
        print(f"  ### {prefix} RSP ################################")
        return result

    return tracer


def http_response(app: App) -> App:
    "Generates an HTTP response, emulating a web server."

    def http(req: Req):
        status, headers, body = app(req)
        out = [f"HTTP/1.1 {status} {response_names.get(status, 'Unknown')}\n"]
        headers["Content-Length"] = sum(map(len, body))
        for k, v in headers.items():
            out.append(f"{header_key(k)}: {v}\n")
        out.append("\n")
        out.extend(body)
        return (status, headers, out)

    return http


def header_key(k: str) -> str:
    "Returns a 'A-Key-Word' for 'a-key-word"
    return re.sub(WORD_RX, lambda m: capitalize(str(m[1])), k.replace("_", "-"))


WORD_RX = re.compile(r"\b([a-z]+)\b")


def capitalize(k: str):
    return k[0].upper() + k[1:]
