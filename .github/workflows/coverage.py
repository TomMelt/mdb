import json
import sys


def get_coverage() -> float:
    with open("cov.json", mode="r") as file:
        coverage = json.load(file)

    return coverage["totals"]["percent_covered"]


if __name__ == "__main__":
    coverage = get_coverage()
    cutoff = float(sys.argv[1])
    if coverage < cutoff:
        print(
            f"Error: pytest code coverage [{coverage:.2f}%] is lower than the required cutoff [{cutoff:.0f}%]."
        )
        exit(1)
    else:
        print(f"Great, code coverage is {coverage:.2f}%! (cutoff is {cutoff:.0f}%)")
