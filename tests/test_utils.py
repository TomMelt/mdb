# Copyright 2023-2026 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

from mdb.utils import (
    collapse_ranges,
    parse_ranks,
    pretty_print_response,
    reduce_response,
    strip_bracketted_paste,
    strip_control_characters,
)


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


def test_collapse_ranges() -> None:
    # consecutive integers collapse to a range
    assert collapse_ranges([1, 2, 3, 4]) == "1-4"

    # single integer
    assert collapse_ranges([5]) == "5"

    # multiple disjoint ranges
    assert collapse_ranges([1, 2, 3, 6, 7, 10, 11, 12]) == "1-3,6-7,10-12"

    # unsorted input is sorted internally
    assert collapse_ranges([12, 10, 11, 7, 6, 3, 2, 1]) == "1-3,6-7,10-12"

    # duplicates are deduplicated
    assert collapse_ranges([1, 1, 2, 2, 3]) == "1-3"

    # empty list returns empty string
    assert collapse_ranges([]) == ""

    # gaps between single values
    assert collapse_ranges([1, 3, 5, 7]) == "1,3,5,7"

    # mix of single values and ranges
    assert collapse_ranges([1, 2, 5, 6, 7, 10]) == "1-2,5-7,10"


def test_pretty_print_response(capsys) -> None:
    response = {
        0: "command ran\r\nline 1\r\nline 2\r\n",
        1: "command ran\r\nline 3\r\n",
    }
    pretty_print_response(response)
    captured = capsys.readouterr()

    assert "0: line 1" in captured.out
    assert "0: line 2" in captured.out
    assert "1: line 3" in captured.out
    assert "*" * 72 in captured.out  # separator between ranks
    # header lines are skipped
    assert "command ran" not in captured.out


def test_reduce_response(capsys) -> None:
    response = {
        0: "header\r\ncommon line\r\nunique to 0\r\n",
        1: "header\r\ncommon line\r\nunique to 1\r\n",
        2: "header\r\ncommon line\r\n",
    }
    reduce_response(response)
    captured = capsys.readouterr()

    # shared line should be prefixed with collapsed rank range
    assert "0-2: common line" in captured.out
    # unique lines should show only their rank
    assert "  0: unique to 0" in captured.out
    assert "  1: unique to 1" in captured.out
    # header line is skipped
    assert "header" not in captured.out


def test_reduce_response_single_rank(capsys) -> None:
    response = {
        3: "header\r\nonly line\r\n",
    }
    reduce_response(response)
    captured = capsys.readouterr()

    assert "3: only line" in captured.out


def test_strip_functions() -> None:
    text = "bt\r\n\x1b[?2004l\r#0  \x1b[33msimple\x1b[m () at \x1b[32msimple-mpi.f90\x1b[m:1\r\n\x1b[?2004h"
    text = strip_bracketted_paste(text)
    text = strip_control_characters(text)

    ans = "bt\r\n#0  simple () at simple-mpi.f90:1\r\n"

    assert text == ans
