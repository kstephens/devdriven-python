from typing import Optional, Self, Iterable, Tuple
from dataclasses import dataclass, field

Position = Tuple[int, int]
Size = Position
Pixel = str


def pos(x: int = 0, y: int = 0) -> Position:
    return (x, y)


def pixel(x: str) -> Pixel:
    if isinstance(x, str):
        assert len(x) == 1
    return x


@dataclass
class Canvas:
    pos: Position = field(default=(0, 0))
    cursor: Position = field(default=(0, 0))
    background: Pixel = field(default=" ")

    def __post_init__(self):
        self._size = (0, 0)
        self._rows = []

    @property
    def rows(self) -> Position:
        return self._rows

    @property
    def size(self) -> Position:
        return self._size

    @size.setter
    def size(self, size: Size) -> Self:
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

    def grow(self, size: Size) -> Self:
        if size[0] > self._size[0] or size[1] > self._size[1]:
            self.size = size
        return self

    def print(self, text: str, **kwargs) -> Self:
        return self.write(text + "\n", **kwargs)

    def write(
        self,
        text: str,
        p: Optional[Position] = None,
        background: Optional[Pixel] = None,
        grow=True,
    ) -> Self:
        if not text:
            return self
        p = p or self.cursor
        lines = text.splitlines()
        y = p[1]
        for line in lines:
            if y >= 0:
                x = p[0]
                if grow:
                    self.grow((x + len(line), y + 1))
                for c in line:
                    if c != background:
                        self.plot(c, (x, y))
                    x += 1
            y += 1
        if text[-1] == "\n":
            y += 1
            x = p[0]
        self.cursor = (x, y)
        return self

    def write_opt(
        self,
        text: str,
        p: Optional[Position] = None,
        background: Optional[Pixel] = None,
        grow=True,
    ) -> Self:
        p = p or self.cursor
        # background = background or self.background
        lines = text.splitlines()
        self.grow((self._size[0], p[1] + len(lines)))
        for line in lines:
            if grow:
                self.grow((p[0] + len(line), p[1] + 1))
            if 0 <= p[1] and p[1] <= self._size[1]:
                if not grow and p[0] + len(text) >= self._size[0]:
                    text = text[:]
                row = list(text)
                if background:
                    row = [background if c == background else c for c in row]
                self._rows[p[1]][p[0] : p[0] + len(row)] = row
            p = (p[0], p[1] + 1)
        self.cursor = p
        return self

    def render_row(self, row: Iterable[Pixel], background: Pixel) -> str:
        return "".join([c or background for c in row])

    def render(self, background: Optional[Pixel] = None) -> str:
        background = background or self.background or " "
        return "\n".join([self.render_row(row, background) for row in self._rows])

    def plot(self, c: Optional[Pixel], p: Position) -> Self:
        if isinstance(c, str):
            assert len(c) == 1
        if pos_in(p, self._size):
            self._rows[p[1]][p[0]] = c
        return self


def pos_in(p: Position, rec: Position):
    return 0 <= p[0] and p[0] < rec[0] and 0 <= p[1] and p[1] < rec[1]
