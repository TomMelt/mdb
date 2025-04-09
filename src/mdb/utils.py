# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import re
from os.path import expanduser
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .backend import DebugBackend


def sort_debug_response(results: dict[int, str]) -> dict[int, str]:
    """Sort debug output by process rank.

    Args:
        response: dict containing the

    Returns:
        The string with bracketted paste escape sequence removed.
    """
    return dict(sorted(results.items()))


def pretty_print_response(response: dict[int, str]) -> None:
    lines = []
    for rank, result in response.items():
        if result:
            lines.append(prepend_ranks(rank=rank, result=result))
    combined_output = (72 * "*" + "\n").join(lines)
    print(combined_output)


def extract_float(line: str, backend: "DebugBackend") -> float:
    float_regex = backend.float_regex
    line = strip_control_characters(line)
    m = re.search(float_regex, line)

    if m:
        try:
            result = float(m.group(1))
        except ValueError:
            print(f"cannot convert variable [{result}] to a float.")
    else:
        msg = "float regex doesn't match following string:\n"
        msg += line

        raise ValueError(msg)
    return result


def prepend_ranks(rank: int, result: str) -> str:
    return "".join(
        [f"{rank}:\t" + line + "\r\n" for line in result.split("\r\n")[1:-1]]
    )


def strip_bracketted_paste(text: str) -> str:
    """Strip bracketted paste escape sequence from text
    (see issue #669 https://github.com/pexpect/pexpect/issues/669).

    Args:
        text: string that contains bracketted paste escape sequence,

    Returns:
        The string with bracketted paste escape sequence removed.
    """
    return re.sub(r"\x1b\[\?2004[lh]\r*", "", text)


def strip_control_characters(text: str) -> str:
    """Strip ANSI control characters from a string.

    Args:
        text: string that contains ANSI control characters.

    Returns:
        The string with ANSI control characters removed.
    """
    return re.sub(r"\x1b\[[\d;]*m", "", text)


def parse_ranks(ranks: str) -> list[int]:
    """Parse a string of ranks into a set of integers. E.g.,
    ``parse_ranks("1,3-5")`` would return the following: ``set(1,3,4,5)``.

    Args:
        ranks: string of ranks using either a mix of comma separation and
          ranges using hyphen.

    Returns:
        A set of ranks represented by integers.
    """
    ranks = re.sub(
        r"(\d+)-(\d+)",
        lambda match: ",".join(
            str(i) for i in range(int(match.group(1)), int(match.group(2)) + 1)
        ),
        ranks,
    )

    return list(set([int(s) for s in ranks.split(",")]))


def ssl_cert_path() -> str:
    return expanduser("~/.mdb/cert.pem")


def ssl_key_path() -> str:
    return expanduser("~/.mdb/key.rsa")
