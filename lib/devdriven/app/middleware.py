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

## Reading Inputs, Writing Outputs

Content = str
Data = Any

### Developer Affordance

#### Tracing

def trace(app: App, ident="", stream=sys.stderr) -> App:
    "Traces requests and responses."
    def indent(msg):
        stream.write(f"{'  ' * TRACE_INDENT[0]}{msg}")
    def log(msg):
        indent(f" #{msg} {ident}\n")
    def pp(data):
        indent("")
        pprint(data, stream=stream)
    def tracing(req: Req) -> Res:
        log(">>>")
        TRACE_INDENT[0] += 1
        pp(req)
        result = app(req)
        log("...")
        pp(result)
        TRACE_INDENT[0] -= 1
        log("<<<")
        return result
    return tracing
TRACE_INDENT = [0]

#### Exception Handling

def capture_exception(app: App, cls=Exception, status=500) -> App:
    def capturing_exception(req: Req) -> Res:
        try:
            return app(req)
        except cls as exc:
            req['captured.exception'] = exc
            return status, {"Content-Type": "text/plain"}, (repr(exc),)
    return capturing_exception

### Reading input

def read_input(app: App, read: Callable[[Any], str]) -> App:
    "Reads input.content."

    def reader(req: Req) -> Res:
        req["input.content"] = read(req)
        return app(req)

    return reader


## Writing Outputs

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
def capitalize(k: str):
    return k[0].upper() + k[1:]
WORD_RX = re.compile(r"\b([a-z]+)\b")



## Decoding Inputs, Encoding Outputs

Encoder = Callable[[Data], Content]
Decoder = Callable[[Content], Data]


def decode_content(app: App, decoder: Decoder, content_types=None, strict=False) -> App:
    """
    Decodes body with decoder(input.content) for content_types.
    If strict and Content-Type is not expected, return 400.
    """

    def decoding_content(req: Req) -> Res:
        req["input.data"] = decoder(req["input.content"])
        content_type = req.get("Content-Type")
        if strict and content_types and content_type not in content_types:
            msg = f"Unexpected Content-Type {content_type!r} : expected: {content_types!r} : "
            return 400, {"Content-Type": 'text/plain'}, (msg,)
        return app(req)
    return decoding_content


def encode_content(app: App, encoder: Encoder, content_type="text/plain") -> App:
    "Encodes body with encoder.  Sets Content-Type."
    def encoding_content(req: Req) -> Res:
        status, headers, body = app(req)
        content = "".join(map(encoder, body))
        headers |= {
            "Content-Type": content_type,
            "Content-Length": len(content),
        }
        return status, headers, [content]
    return encoding_content


## Decode JSON, Encode JSON

def decode_json(app: App, **kwargs) -> App:
    "Decodes JSON content."
    def decoding_json(content: Content) -> Any:
        return json.loads(content, **kwargs)
    return decode_content(app, decoding_json, content_types={'application/json', 'text/plain'}, strict=True)


def encode_json(app: App, **kwargs) -> App:
    "Encodes data as JSON."
    def encoding_json(data: Data) -> Content:
        return json.dumps(data, **kwargs) + "\n"
    return encode_content(app, encoding_json, content_type='application/json')

def capture_exception(app: App, status=500, cls=Exception) -> App:
    "Captures any exception and creates a text/plain error document."

    def capturing_exception(req: Req) -> Res:
        try:
            return app(req)
        # pylint: disable-next=broad-exception-caught
        except cls as exc:
            return status, {"Content-Type": "text/plain"}, [f"ERROR: {exc}"]

    return capturing_exception


## Injection

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

### Adapters

def read_wsgi(app: App) -> App:
    return read_input(app, lambda req: req["wsgi.input"].read())
