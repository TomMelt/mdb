# How to contribute

Awesome :sunglasses:, you want to help make `mdb` better. Please read these guidelines on how to get involved!

## Reporting Bugs

1. Use the GitHub issue search -- check if the issue has already been reported.
2. Check if the issue has been fixed -- try to reproduce it with the latest `main` branch.
3. Isolate the problem -- ideally create a [minimal reproducible example](https://stackoverflow.com/help/minimal-reproducible-example) (MWE).
4. Raise an issue with as much information as possible (including your MWE) and label it as `bug`.

A good bug report should contain all the information necessary to allow a developer to reproduce the issue, without needing to
ask for further information. Please try to be as detailed as possible in your report. What is your environment? What steps will
reproduce the issue? What gdb version, MPI library, python version and OS experience the problem? What is the expected outcome?
All of these details assist the process of investigating and fixing bugs.

## Requesting Features

Feature requests are welcome, `mdb` is under active development. My personal ambition is to make `mdb` a powerful debugger for
MPI applications, whilst also trying to take advantage of as much of `gdb`'s built-in features as possible.

Raise an issue to request a feature.

## Adding a Debugger Backend

To integrate a new debugger backend, add a new Python file to the `src/mdb/plugins/` folder, named after the debugger (`[debugger-name].py`). Inside this file, define a class that extends `DebugBackend` to provide an interface for interacting with your debugger and specify its properties.

## Submitting Pull Requests

Good pull requests—patches, improvements, new features—are a fantastic help. They should remain focused in scope and avoid
containing unrelated commits.

Always write a clear log message for your commits. One-line messages are fine for small changes, but bigger changes should look
like this:

    $ git commit -m "A brief summary of the commit
    > 
    > A paragraph describing what changed and its impact."


**Please ask first** before embarking on any significant pull request (e.g. implementing features, refactoring code), otherwise
you risk spending a lot of time working on something that may not be suitable for this project. (If you feel you want to take
`mdb` in a vastly different direction, feel free to make a fork).

Please adhere to the [coding conventions](#Coding-Conventions) used in this project.

Before merging, pull requests are required to pass all continuous integration.

## Testing

[pytest](https://docs.pytest.org/en/latest/contents.html) is used as a testing framework. The tests will be run as part of the
GitHub CI. If you are doing development work, please install the developer version of `mdb` and run the tests locally to make
sure they pass before submitting your PR. Furthermore, please write tests for any new source code that you add.

You can run the existing tests (and your new ones) with the following command:

```shell
$ pytest --cov-report term-missing --cov=mdb -vv tests/
```

The coverage report (`--cov-report term-missing`) will help ensure that new features are added with tests. You should see
something like this:

```shell
$ pytest --cov-report term-missing --cov=mdb -vv tests/
=========================================================== test session starts ============================================================
platform linux -- Python 3.12.0, pytest-7.4.4, pluggy-1.3.0 -- /home/melt/miniconda3/envs/mdb/bin/python
cachedir: .pytest_cache
rootdir: /home/melt/sync/cambridge/projects/side/mdb
plugins: cov-4.1.0
collected 5 items

tests/test_integration.py::test_mdb_simple PASSED
[ 20%]
tests/test_integration.py::test_mdb_timeout PASSED
[ 40%]
tests/test_utils.py::test_parse_ranks PASSED
[ 60%]
tests/test_utils.py::test_strip_functions PASSED
[ 80%]
tests/test_utils.py::test_print_tabular_output PASSED
[100%]

---------- coverage: platform linux, python 3.12.0-final-0 -----------
Name                Stmts   Miss  Cover   Missing
-------------------------------------------------
mdb/__init__.py         0      0   100%
mdb/mdb.py              8      0   100%
mdb/mdb_attach.py      34      2    94%   89-90
mdb/mdb_client.py      71      3    96%   16-18, 114
mdb/mdb_launch.py      39     13    67%   44-50, 56-67
mdb/mdb_shell.py      219     54    75%   30-33, 72-89, 108-110, 123-146, 173-174, 201-206, 284-285, 300-307, 378, 390, 454-455
mdb/utils.py           16      0   100%
-------------------------------------------------
TOTAL                 387     72    81%


============================================================ 5 passed in 13.97s ============================================================
```

The key point is all tests should pass and `TOTAL` coverage should stay above 60%. If the coverage drops below 60% then the
GitHub CI will fail.

## Coding conventions

I use [black](https://black.readthedocs.io/en/stable/index.html) and [flake8](https://flake8.pycqa.org/en/latest/) to enforce
consistent style. In general I try to use _sensible_ naming conventions although I appreciate that the exact meaning of
_sensible_ is hard to condense into words. Please use your best judgement and look at the rest of the code for inspiration.

The GitHub CI is setup to check for compliance with `black`, `flake8` and `mypy`. To check modifications to the code locally,
without relying on the CI, please follow the [developer installation instructions](README.md#Developers). Then you should be
able to run the following to check for code compliance.

```shell
flake8 .
black --check .
mypy --strict .
```

Please resolve any errors before creating a pull request, or requesting code review.

### Docstrings and Documentation

`mdb` currently uses 3 conventions for docstrings/documentation. Each style is used for a specific purpose.

* [`click`-style](https://click.palletsprojects.com/en/8.1.x/documentation/#documenting-scripts) is used for the command line
  interface (CLI). This means that useful help text can be autogenerated by the Click package. When modifying Click commands
  please use this style of documentation.
* `cmd`-style : Python's [`cmd`](https://docs.python.org/3/library/cmd.html) package uses the
  [`do_help`](https://docs.python.org/3/library/cmd.html#cmd.Cmd.do_help) method to display useful information for a given
  command. When modifying `cmd` commands please use a similar style to the rest of the `cmd` commands.
* [`google`-style](https://google.github.io/styleguide/pyguide.html#381-docstrings) : for everything else I use Google's style
  convention. Later on in this project I may replace the `cmd` style docstrings and just use Google's style for everything.

Thanks, Tom
