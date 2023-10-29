from devdriven.cli import Main, Command

class MainTest(Main):
  def make_command(self, argv):
    name = argv.pop(0)
    return ExampleTest(self).parse_argv(argv).set_name(name)

  def emit_output(self, output):
    self.output = output
    self.exit_code = 0

class ExampleTest(Command):
  def run(self):
    rtn = ['OK', self.args, self.opts]
    if self.args and self.args[0] == 'RAISE':
      raise Exception("ERROR")
    return rtn

def test_results():
  argv = 'cmd1 -flag --a=1 --b 2 arg1 arg2 -- --foo=bar, cmd2 a b, cmd3 RAISE error'.split(' ')
  main = MainTest().run(argv)
  # print(repr(main.output))
  expected = {
    'errors': [
      ['cmd3', 'ERROR']
    ],
    'result': [
      ['cmd1',
        ['OK',
          ['arg1', 'arg2', '--foo=bar'],
          {'flag': True, 'a': '1', 'b': '2'}]],
      ['cmd2', ['OK', ['a', 'b'], {}]]
    ]
  }
  assert main.output == expected
