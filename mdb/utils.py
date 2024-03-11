# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import re
from os.path import expanduser


def sort_debug_response(response):
    output = response["result"]
    output = sorted(output, key=lambda result: result["rank"])
    return output


def pretty_print_response(response):
    lines = []
    for result in response:
        lines.append(prepend_ranks(output=result["result"], rank=result["rank"]))
    combined_output = (72 * "*" + "\n").join(lines)
    print(combined_output)


def extract_float(line, backend):
    float_regex = backend.float_regex
    match = re.search(float_regex, line)
    if match:
        try:
            result = float(match.group(1))
        except ValueError:
            print(f"cannot convert variable [{result}] to a float.")
    return result


def prepend_ranks(output, rank):
    output = "".join(
        [f"{rank}:\t" + line + "\r\n" for line in output.split("\r\n")[1:-1]]
    )
    return output


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


def parse_ranks(ranks: str) -> set[int]:
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

    return set([int(s) for s in ranks.split(",")])


def print_tabular_output(strings: list[str], cols: int = 32) -> None:
    """Print tabular text for a list of strings. Coloumns will all be the same
    length determined by the width of the largest string.

    Args:
        strings: list of strings to be formatted into columns.
        cols (optional): number of columns in output. Defaults to 32.

    Returns:
        None.
    """

    max_width: int = max(map(len, strings))
    num_rows: int = (len(strings) - 1) // cols + 1
    for i in range(num_rows):
        current_row: list[str] = strings[i * cols : (i + 1) * cols]
        text: list[str] = list(map(lambda x: f"{x: >{max_width}}", current_row))
        print(" ".join(text))
    return


def ssl_cert_path() -> str:
    return expanduser("~/.mdb/cert.pem")


def ssl_key_path() -> str:
    return expanduser("~/.mdb/key.rsa")
