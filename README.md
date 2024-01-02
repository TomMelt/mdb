# mdb

An MPI debugger built on [`gdb`](https://www.sourceware.org/gdb/).

# Purpose

`mdb` is a debugger aimed at parallel programs using the MPI programming paradigm. `mdb` acts as a wrapper around `gdb` and, as
such, it supports the following languages:

* C
* C++
* Fortran

Technically `gdb` supports other languages as well, but this is the intersection of languages that MPI is implemented in.

# Usage

First run `mdb` in launch mode as part of your normal program run.

```bash
mpirun -n 8 mdb launch ./a.out
```

In a separate terminal (and even separate machine if you wish (but you'd need to use SSH)) use `mdb` in attach mode.

```bash
mdb attach -n 8 -s 0,2-4
```

This will run the debugger with 8 processes in total but only specific processes [0,2,3,4] have been selected (`-s`) for
interactive debugging. The other processes will run but `mdb` will not interact with them.

`mdb` uses a default host of `--host localhost` and a default starting port of `--port 2000`. You can see full CLI options
using:

```bash
mdb launch --help
mdb attach --help
```

I have tried to keep the commands similar to `gdb`. I will upload a video (or asciinema) tutorial shortly to demonstrate a
typical debugging session and the features of `mdb`.

# Installation

These instructions are for normal use of `mdb`. Please see [below](#Developers) for a developer install.

1. Clone the repository.

    ```bash
    git clone https://github.com/TomMelt/mdb.git
    ```

2. (optional - but recommended) Create a conda environment or venv.

    ```bash
    conda create -n mdb python
    conda activate mdb
    ```

3. Install `mdb`.

    ```bash
    cd mdb/
    pip install -e .
    ```

## Dependencies

The main dependencies are (see [`requirements.txt`](requirements.txt)):

* `click`
* `matplotlib`
* `numpy`
* `pexpect`
* `youplot`/`uplot` (optional but recommended for fancy ascii plots - see [here](https://github.com/red-data-tools/YouPlot) for
  installation instructions)

# Supported MPI implementations

Currently I am building and testing for open MPI only. In principle it really won't take much work to expand to other
implementations but I just haven't done it yet.

- [x] open MPI mpirun
- [x] intel MPI mpirun
- [x] slurm srun
- [ ] mpiexec ?
- [ ] others...

# TODO

- [x] handle session termination and CTRL-C signalling better
- [ ] add tests
- [ ] expand docs
- [ ] record asciinema demo? / youtube video?
- [x] add CI
- [ ] expand README
- [x] restructure code to remove global vars
- [x] add support for other MPI launchers (intel MPI, mpiexec, srun etc?)

# Contributing

If you would like to be involved in the development, feel free to submit a PR. A word of caution though... the code is currently
in a highly volatile state and a plan major changes to the interface and layout. I will update this section when I reach a more
stable part of the development. Either way changes are welcome at anytime.

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for more details on how best to contribute.

# Developers

For development it is best to install `mdb` with some additional dependencies. These can be installed using the same
`setup.py` file. For developer install please use the following command:

```bash
pip install -e .[develop]
```

This will install additional dependencies, namely, `black`, `flake8` and `mypy`.

* [`black`](https://black.readthedocs.io/en/stable/) is used for formatting the source code and I let `black` have the final say on formatting decisions. I do not use
  manual override e.g., `# fmt: off` (see [black documentation](https://black.readthedocs.io/en/stable/usage_and_configuration/the_basics.html)).
* [`flake8`](https://flake8.pycqa.org/en/latest/) is used to check the style and quality of some python code. I use default settings with two exceptions. That is, I
  ignore errors `E203` and `E501`. `E501` is `Line too long` and whilst I try to keep a maximum line length of 99 it is often
  not sensible to force this. `E203` is `Whitespace before ':'`, which gets incorrectly triggered for array slices (see
[here](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html#slices) for more info)
* [`mypy`](https://mypy.readthedocs.io/en/stable/) is a static type checker and is used to help ensure that variables and functions are being used correctly.

# Acknowledgements

This project was inspired by @mystery-e204's [mpidb](https://github.com/mystery-e204/mpidb) tool and @Azrael3000's
[tmpi](https://github.com/Azrael3000/tmpi) tmux interface.

# Similar Projects

I have recently come across @robertu94's [mpigdb](https://github.com/robertu94/mpigdb). It seems to offer similar functionality
and it has a closer integration with gdb using gdb's inbuilt `inferior`s to handle multiple processes at the same time (see
[gdb manual sec. 4.9](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Inferiors-Connections-and-Programs.html#Inferiors-Connections-and-Programs)
for more info). The main difference from my perspective is that I can plot variables across mpi processes using `mdb` and AFAIK
`mpigdb` cannot. If you like `mdb` you may want to check out `mpigdb` as well.
