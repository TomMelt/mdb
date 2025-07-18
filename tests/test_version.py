import os
import subprocess

try:
    import tomllib
except ModuleNotFoundError:
    # Remove this once minimum Python version is 3.11
    import pip._vendor.tomli as tomllib


def test_version_number():
    git_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    print(git_root)

    with open(os.path.join(git_root, "pyproject.toml"), "rb") as f:
        version = tomllib.load(f)["project"]["version"].strip()

    assert (
        version == subprocess.check_output("mdb version", shell=True).decode().strip()
    )
