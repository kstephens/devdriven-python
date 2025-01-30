import re

GLOB_RX = re.compile(
    r"(?P<dot>\.)|(?P<char>\?)|"  # +
    r"(?P<star_star>(?P<pre_star_star>^|/)\*\*)|"  # +
    r"(?P<begin_star>(?P<pre_star>^|/)\*)|(?P<star>\*)"  #
)


def glob_to_regex(glob: str, deep_matches_empty: bool = False) -> re.Pattern:
    def scan(m: re.Match):
        # print(repr(m.groupdict()))
        if m["dot"]:
            return r"\."
        if m["char"]:
            return r"[^/.]"
        if m["star_star"]:
            if deep_matches_empty:
                return m["pre_star_star"] + r".*?"
            return m["pre_star_star"] + r".+?"
        if m["begin_star"]:
            return m["pre_star"] + r"(?![./])[^/]*"
        if m["star"]:
            return r"(?:[^/]*)"
        assert not "here"
        return None

    return re.compile("^(?:" + re.sub(GLOB_RX, scan, glob) + ")$")
