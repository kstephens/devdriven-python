from ..asserts import assert_output_by_key
from . import canvas as sut


def test_canvas():
    run_test("test_canvas", run_test_canvas)


def run_test_canvas(prt):
    c = sut.Canvas()
    si = 0

    def s():
        nonlocal si
        si += 1
        prt("\n##########################")
        prt(f"# {si!r}")
        prt(f"# size={c.size!r}")
        prt(f"# cursor={c.cursor!r}")
        for row in c.rows:
            prt(f"#{c.render_row(row, '_')}#")
        prt("############################\n")

    s()

    c.print("O:::")
    s()

    c.grow((20, 12))
    s()

    c.plot("x", (3, 7))
    c.plot("y", (8, 2))
    s()

    for i in range(2, 6):
        c.plot(str(i), (i, i))
    s()

    c.print(" abc\n  123 ")
    s()
    prt(c.render(background="_"))

    c.print(" xyz \n  567 ", p=(8, 5), background=" ")
    s()
    prt(c.render())


def run_test(name, test_fun):
    def proc(actual_out):
        with open(actual_out, "w", encoding="utf-8") as out:

            def prt(x):
                print(x, file=out)

            test_fun(prt)

    assert_output_by_key(name, "tests/output/ascii", proc)
