import re


def strip_bracketted_paste(text):
    # strip bracketted paste
    # (see issue #669 https://github.com/pexpect/pexpect/issues/669)
    return re.sub(r"\x1b\[\?2004[lh]\r*", "", text)


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
