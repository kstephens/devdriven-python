"""
Application middleware combinators inspired Python WSGI and Ruby Rack.

An "App" is anything callable with a single "request" argument.
It returns a "response": a status code, headers, body.
A request ("Req") is a MutableMapping[str, Any]: e.g. `dict`.
Applications and middleware follow the same protocol.
Combinators create new Apps by wrapping others.
This pattern is not limited to web apps, it can be used for command line applications.

# A simple `App`:

def simple_app(Req: req) -> Res:
    "A simple app."
    x, y = [int(req["input.data"][k]) for k in ("x", "y")]
    return 200, {"Content-Type": "text/plain"}, [str(x * y)]

Input combinators follow this pattern:

def compose_input_handler(app: App) -> App:
    def input_handler(req: Req) -> Res:
       do_something_with_input(req)
       return app(req)
  return input_handler

Output combinators follow this pattern:

def compose_output_handle(app: App) -> App
    def output_handler(req: Req) -> Res:
       status, headers, body = app(req)
       # alter status, header, body in some manner.
       return status, headers, body
  return output_handler

A web stack composition:

app = simple_app
app = encode_json(app)
app = decode_json(app)
app = capture_exception(app)
req = {'input.content': '{"x": 2, "y": 3}'}
status, headers, body = app(req)
assert status == 200
assert headers == {'Content-Type': 'application/json'}
assert list(body) == ['6']

"""

from typing import Any, MutableMapping, Tuple, Iterable, Callable, Optional
import json
import re
import sys
from datetime import datetime
import traceback
from email.utils import formatdate
from pprint import pprint
from http.client import responses as response_names
import yaml

# from icecream import ic

Status = int
Headers = MutableMapping[str, Any]
Body = Iterable
Res = Tuple[Status, Headers, Body]
Req = MutableMapping[str, Any]
App = Callable[[Req], Res]


# ### Developer Affordance


def is_success(status: Status) -> bool:
    return status in range(200, 300)


# #### Exception Handling


def capture_exception(app: App, status=500, cls=Exception, with_traceback=False) -> App:
    "Captures any exception and creates a text/plain error document."

    def _capture_exception(req: Req) -> Res:
        try:
            return app(req)
        # pylint: disable-next=broad-exception-caught,broad-except
        except cls as exc:
            req["captured.exception"] = exc
            body = [f"ERROR: {exc}"]
            if with_traceback:
                trb = exc.__traceback__
                trb_extracted = traceback.extract_tb(trb)
                lines = traceback.format_list(trb_extracted)
                body.extend(lines)
            return status, {"Content-Type": "text/plain"}, body

    return _capture_exception


# #### Tracing


def trace(app: App, ident="", stream=sys.stderr) -> App:
    "Traces requests and responses."

    def indent(msg):
        stream.write(f"{'  ' * TRACE_INDENT[0]}{msg}")

    def log(msg):
        indent(f" #{msg} {ident}\n")

    def prnt(data):
        indent("")
        pprint(data, stream=stream)

    def _trace(req: Req) -> Res:
        log(">>>")
        TRACE_INDENT[0] += 1
        prnt(req)
        result = app(req)
        log("...")
        prnt(result)
        TRACE_INDENT[0] -= 1
        log("<<<")
        return result

    return _trace


TRACE_INDENT = [0]

# ## Reading Input, Writing Output

Content = str
Data = Any

# ### Reading input


def read_input(app: App, read: Optional[Callable[[Data], Content]] = None) -> App:
    "Reads body.stream"
    if not read:
        # pylint: disable-next=unnecessary-lambda-assignment
        read = lambda stream: stream.read()

    def _read_input(req: Req) -> Res:
        assert read is not None
        req["input.content"] = read(req["input.stream"])
        return app(req)

    return _read_input


# ### Writing Output


def write_output(app: App) -> App:
    "Writes body to output.stream."

    def _write_output(req: Req) -> Res:
        stream = req.pop("output.stream")
        status, headers, body = app(req)
        for item in body:
            stream.write(str(item))
        return status, headers, body

    return _write_output


def http_response(app: App) -> App:
    "Generates an HTTP response, emulating a web server."

    def _http_response(req: Req) -> Res:
        status, headers, body = app(req)
        out = [f"HTTP/1.1 {status} {response_names.get(status, 'Unknown')}\n"]
        for k, v in headers.items():
            out.append(f"{k}: {v}\n")
        out.append("\n")
        out.extend(body)
        return status, headers, out

    return _http_response


def capitalize_headers(app: App) -> App:
    "Capitalizes-All-Headers."

    def _capitalize_headers(req: Req) -> Res:
        status, headers, body = app(req)
        headers = {header_key(k): v for k, v in headers.items()}
        return status, headers, body

    return _capitalize_headers


def header_key(k: str) -> str:
    "Returns a 'A-Key-Word' for 'a-key-word"
    return re.sub(WORD_RX, lambda m: capitalize(str(m[1])), k.replace("_", "-"))


def capitalize(k: str):
    return k[0].upper() + k[1:]


WORD_RX = re.compile(r"\b([a-z]+)\b")


# ## Decoding Inputs, Encoding Outputs

Encoder = Callable[[Data], Content]
Decoder = Callable[[Content], Data]


def decode_content(app: App, decoder: Decoder, content_types=None, strict=False) -> App:
    """
    Combinator decodes body with decoder(input.content) for content_types.
    If strict and Content-Type is not expected, return 400.
    """

    def _decode_content(req: Req) -> Res:
        req["input.data"] = decoder(req["input.content"])
        content_type = req.get("Content-Type")
        if strict and content_types and content_type not in content_types:
            msg = f"Unexpected Content-Type {content_type!r} : expected: {content_types!r} : "
            return 400, {"Content-Type": "text/plain"}, (msg,)
        return app(req)

    return _decode_content


def encode_content(app: App, encoder: Encoder, content_type: str) -> App:
    "Combinator encodes body with encoder.  Sets Content-Type."

    def _encode_content(req: Req) -> Res:
        status, headers, body = app(req)
        if not body:
            content = encoder(headers.pop("output.data"))
        else:
            content = "".join(map(encoder, body))
        headers.update(
            {
                "Content-Type": content_type,
                "Content-Length": len(content),
            }
        )
        return status, headers, (content,)

    return _encode_content


# ## Decode JSON, Encode JSON


def decode_json(app: App, **kwargs) -> App:
    "Decodes JSON content."

    def _decode_json(content: Content) -> Any:
        return json.loads(content, **kwargs)

    return decode_content(
        app, _decode_json, content_types={"application/json", "text/plain"}, strict=True
    )


def encode_json(app: App, **kwargs) -> App:
    "Encodes data as JSON."

    def _encode_json(data: Data) -> Content:
        return json.dumps(data, **kwargs) + "\n"

    return encode_content(app, _encode_json, content_type="application/json")


# ## Decode YAML, Encode YAML


def decode_yaml(app: App, **kwargs) -> App:
    """
    Decodes YAML content.
    "Loader" option default is yaml.FullLoader.
    If "multiple_documents" option is True, parse one or more documents,
    otherwise expect only one document.
    """

    kwargs = {"Loader": yaml.FullLoader} | kwargs
    multiple_documents = kwargs.get("multiple_documents", False) is not False

    def _decode_yaml(content: Content) -> Any:
        documents = list(yaml.load_all(content, **kwargs))
        if multiple_documents:
            return documents
        assert len(documents) == 1
        return documents[0]

    return decode_content(
        app,
        _decode_yaml,
        content_types={"application/yaml", "text/yaml", "text/plain"},
        strict=True,
    )


def encode_yaml(app: App, **kwargs) -> App:
    """
    Encodes data as YAML.
    Note: this includes the "..." end of document footer.
    """

    def _encode_yaml(data: Data) -> Content:
        return yaml.dump(data, **kwargs)

    return encode_content(app, _encode_yaml, content_type="application/yaml")


# ## Header Management


def content_length(app: App) -> App:
    def _content_length(req: Req) -> Res:
        status, headers, body = app(req)
        headers["Content-Length"] = sum(map(len, body))
        return status, headers, body

    return _content_length


# # Injection


# ## Request Injection


def default_req(app: App, defaults: Req) -> App:
    "Defaults any req values that are not defined."

    def _default_req(req: Req):
        return app(default_dict(req, defaults))

    return _default_req


def override_req(app: App, overrides: Req) -> App:
    "Overrides req values."

    def _override_req(req: Req):
        req.update(overrides)
        return app(req)

    return _override_req


ResOptional = Tuple[Optional[Status], Optional[Headers], Optional[Body]]
AppOptional = Callable[[Req], ResOptional]


# ## Response Injection


def default_res(app: AppOptional, defaults: ResOptional) -> App:
    "Defaults any values that are not defined."

    def _default_res(req: Req):
        status_, headers_, body_ = defaults
        status, headers, body = app(req)
        if status is None and status_ is not None:
            status = status_
        if headers_:
            default_dict(headers, headers_)
        if body is None and body_ is not None:
            body = body_
        return status, default_dict(headers, defaults), body

    return _default_res


def override_res(app: App, overrides: ResOptional) -> App:
    "Overrides response status, headers, body."

    def _override_res(req: Req):
        status_, headers_, body_ = overrides
        status, headers, body = app(req)
        if status_ is not None:
            status = status_
        if headers_:
            headers.update(headers_)
        if body_ is not None:
            body = body_
        return status, headers, body

    return _override_res


def default_dict(d, defaults):
    for k, v in defaults.items():
        if k not in d:
            d[k] = v
    return d


# ## Composition


# ### Adapters


def read_wsgi(app: App) -> App:
    return read_input(app, lambda req: req["wsgi.input"].read())


# ## HTTP Support


def http_date_header(app: App, now: Callable[[], datetime] = datetime.now) -> App:
    "Adds a HTTP compliant 'Date:' header."

    def _http_date_header(req: Req) -> Res:
        status, headers, body = app(req)
        date = now()
        headers["Date"] = formatdate(
            timeval=date.timestamp(), localtime=False, usegmt=True
        )
        return status, headers, body

    return _http_date_header
