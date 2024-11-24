from io import StringIO
from . import middleware as sut
from pprint import pprint
# from icecream import ic

def test_stack():
  def something_useful_app(req: sut.Req) -> sut.Res:
    x, y = req['input.data']
    return 200, {}, (x * y,)

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

  app = app
  req = {
    'input.stream': StringIO('["ab", 5]'),
    'output.stream': StringIO(""),
    'Content-Type': 'application/json',
    }
  actual = app(req)
  pprint(actual)
  expected =   (200,
 {'Content-Length': 13, 'Content-Type': 'application/json'},
 ['HTTP/1.1 200 OK\n',
  'Content-Type: application/json\n',
  'Content-Length: 13\n',
  '\n',
  '"ababababab"\n'])
  assert actual == expected

  actual = req['output.stream'].getvalue()
  expected = """
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 13

"ababababab"
"""[1:]
  print(actual)
  pprint(actual)
  assert actual == expected
