# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

from mdb.utils import parse_ranks, strip_bracketted_paste, strip_control_characters


def test_parse_ranks() -> None:
    input_str = "0,1-4,7"
    ranks = parse_ranks(input_str)
    assert ranks == [0, 1, 2, 3, 4, 7]

    input_str = "8"
    ranks = parse_ranks(input_str)
    assert ranks == [8]

    input_str = "4,3,2"
    ranks = parse_ranks(input_str)
    assert ranks == [2, 3, 4]


def test_strip_functions() -> None:
    text = "bt\r\n\x1b[?2004l\r#0  \x1b[33msimple\x1b[m () at \x1b[32msimple-mpi.f90\x1b[m:1\r\n\x1b[?2004h"
    text = strip_bracketted_paste(text)
    text = strip_control_characters(text)

    ans = "bt\r\n#0  simple () at simple-mpi.f90:1\r\n"

    assert text == ans
