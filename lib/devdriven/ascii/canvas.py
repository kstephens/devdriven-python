from typing import Optional


class Canvas:
    def __init__(self):
        self.pos = (0, 0)
        self._size = (0, 0)
        self._rows = []
        self.cursor = (0, 0)
        self.background = None

    @property
    def rows(self):
        return self._rows

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, size):
        size_curr = self._size
        size_delta = (size[0] - size_curr[0], size[1] - size_curr[1])

        if size_delta[1] > 0:
            more_rows = [[None] * size[0] for _i in range(size_delta[1])]
            self._rows.extend(more_rows)
        if size_delta[1] < 0:
            self._rows[size[1] :] = []

        if size_delta[0] > 0:
            for line in self._rows:
                line[size_curr[0] :] = [None] * size_delta[0]
        if size_delta[0] < 0:
            for line in self._rows:
                line[size[0] :] = []

        self._size = size
        return self

    def grow(self, size: tuple):
        if size[0] > self._size[0] or size[1] > self._size[1]:
            self.size = size
        return self

    def print(self, text: str, **kwargs):
        return self.write(text + "\n", **kwargs)

    def write(self, text: str, pos=None, background=None, grow=True):
        if not text:
            return self
        pos = pos or self.cursor
        lines = text.splitlines()
        y = pos[1]
        for line in lines:
            if y >= 0:
                x = pos[0]
                if grow:
                    self.grow((x + len(line), y + 1))
                for c in line:
                    if c != background:
                        self.plot(c, (x, y))
                    x += 1
            y += 1
        if text[-1] == "\n":
            y += 1
            x = pos[0]
        self.cursor = (x, y)
        return self

    def write_opt(self, text: str, pos=None, background=None, grow=True):
        pos = pos or self.cursor
        # background = background or self.background
        lines = text.splitlines()
        self.grow((self._size[0], pos[1] + len(lines)))
        for line in lines:
            if grow:
                self.grow((pos[0] + len(line), pos[1] + 1))
            if 0 <= pos[1] and pos[1] <= self._size[1]:
                if not grow and pos[0] + len(text) >= self._size[0]:
                    text = text[:]
                row = list(text)
                if background:
                    row = [background if c == background else c for c in row]
                self._rows[pos[1]][pos[0] : pos[0] + len(row)] = row
            pos = (pos[0], pos[1] + 1)
        self.cursor = pos
        return self

    def render_row(self, row, background):
        return "".join([c or background for c in row])

    def render(self, background: Optional[str] = None):
        background = background or self.background or " "
        return "\n".join([self.render_row(row, background) for row in self._rows])

    def plot(self, c: Optional[str], pos: tuple):
        if isinstance(c, str):
            assert len(c) == 1
        if pos_in(pos, self._size):
            self._rows[pos[1]][pos[0]] = c
        return self


def pos_in(pos: tuple, rec: tuple):
    return 0 <= pos[0] and pos[0] < rec[0] and 0 <= pos[1] and pos[1] < rec[1]


def test():
    c = Canvas()

    def s():
        print("\n============================\n")
        # ic(c.cursor)
        # ic(c.size)
        for row in c.rows:
            print(c.render_row(row, "_"))
        print("\n============================\n")

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
    print(c.render(background="_"))

    c.print(" xyz \n  567 ", pos=(8, 5), background=" ")
    s()
    print(c.render())


test()
