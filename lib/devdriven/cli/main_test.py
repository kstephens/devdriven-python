from . import Main, Command


class MainTest(Main):
    def make_command(self, argv):
        instance = ExampleTest()
        instance.name = argv.pop(0)
        return instance.parse_argv(argv)

    def capture_exceptions(self, _command):
        return True

    def emit_output(self, output):
        self.output = output
        self.exit_code = 0


class ExampleTest(Command):
    def exec(self):
        rtn = ["OK", self.args, self.opts]
        if self.args and self.args[0] == "RAISE":
            raise Exception("ERROR")
        return rtn


def test_results():
    argv = "test.exe cmd1 -flags --a=1 --b 2 3 -5 arg1 arg2 -- --foo=bar, cmd2 a b, cmd3 RAISE error".split(
        " "
    )
    main = MainTest().run(argv)
    # print(repr(main.output))
    expected = {
        "errors": [["cmd3", {"class": "Exception", "message": "ERROR"}]],
        "result": [
            [
                "cmd1",
                [
                    "OK",
                    ["--b", "2", "3", "-5", "arg1", "arg2", "--foo=bar"],
                    {"a": "1", "f": True, "g": True, "l": True, "s": True},
                ],
            ],
            ["cmd2", ["OK", ["a", "b"], {}]],
        ],
    }
    assert main.output == expected
