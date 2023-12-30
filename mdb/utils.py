import re


def strip_bracketted_paste(text):
    """
    strip bracketted paste escape sequence from text
    (see issue #669 https://github.com/pexpect/pexpect/issues/669)
    """
    return re.sub(r"\x1b\[\?2004[lh]\r*", "", text)


def strip_control_characters(text):
    return re.sub(r"\x1b\[[\d+\[m]+", "", text)


def parse_ranks(ranks):
    ranks = re.sub(
        r"(\d+)-(\d+)",
        lambda match: ",".join(
            str(i) for i in range(int(match.group(1)), int(match.group(2)) + 1)
        ),
        ranks,
    )
    ranks = set([int(s) for s in ranks.split(",")])

    return ranks


def tabular_output(strings, cols=32):
    """
    create tabular text for a list of strings.
    """

    max_width = max(map(len, strings))
    num_rows = (len(strings) - 1) // cols + 1
    for i in range(num_rows):
        current_row = strings[i * cols : (i + 1) * cols]
        text = list(map(lambda x: f"{x: >{max_width}}", current_row))
        print(" ".join(text))

    return
