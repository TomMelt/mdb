# mdb

[![tests](https://github.com/TomMelt/mdb/actions/workflows/tests.yml/badge.svg)](https://github.com/TomMelt/mdb/actions/workflows/tests.yml)
[![style](https://github.com/TomMelt/mdb/actions/workflows/code-validation.yml/badge.svg?branch=main)](https://github.com/TomMelt/mdb/actions/workflows/code-validation.yml)
[![readthedocs](https://readthedocs.org/projects/mdb/badge/?version=latest)](https://mdb.readthedocs.io/en/latest/?badge=latest)

An MPI-aware frontend for serial debuggers, such as [`gdb`](https://www.sourceware.org/gdb/) and [`lldb`](https://lldb.llvm.org).

# Documentation

For help with installation, a quick-start tutorial (with example debug session) and an API reference please check out `mdb`'s
[documentation](https://mdb.readthedocs.io/en/latest/).

# Purpose

`mdb` is a debugger aimed at parallel programs using the MPI programming paradigm. `mdb` acts as a MPI-aware frontend for
different backend debuggers, such as `gdb` and `lldb`. As such, it supports the following languages:

* C
* C++
* Fortran

Technically `gdb` supports other languages as well, but this is the intersection of languages that MPI is implemented in. For
`lldb` your mileage may vary when debugging Fortran.

# Usage

Please see the [quick start guide](https://mdb.readthedocs.io/en/latest/quick-start.html#quick-start) in the documentation for a
walk-through of a simple debug session. The guide covers basic debug commands and information on how to launch the debugger.

# Installation

These instructions are for normal use of `mdb`. Please see [below](#Developers) for a developer install.

1. Clone the repository.

    ```bash
    git clone https://github.com/TomMelt/mdb.git
    ```

2. (optional - but recommended) Create and activate a virtual environment.

    ```bash
    python3 -m venv .mdb
    source .mdb/bin/activate
    ```

3. Install `mdb`.

    ```bash
    cd mdb/
    pip install .[termgraph]
    ```

More information can be found in the [installation
guide](https://mdb.readthedocs.io/en/latest/installation.html#installing-mdb).

**Please Note** `mdb` doesn't currently support Windows (see
[here](https://mdb.readthedocs.io/en/latest/installation.html#windows-support) for more info).

# Known Issues

* Doesn't work with `lldb` version 18. It does work with versions 17 and 20 however (version 19 wouldn't install on my machine so
  I couldn't test it).
* Doesn't work with intel MPI yet (open issue
  [here](https://community.intel.com/t5/Intel-MPI-Library/Issue-when-using-intel-MPI-through-my-debugger-mdb/m-p/1663320#M12060)).
  A possible workaround would be to try using mpich to launch instead of Intel's `mpiexec`. Note that you will need to use a
  recent version of mpich (see below).
* Due to a bug in mpich `mdb` only supports `>=4.3.2` - see [#65](https://github.com/TomMelt/mdb/issues/65) for more info)
* If you encounter issues with SSL/TLS certificate generation (`RuntimeError: Failed to generate SSL certificate.`), you
  can specify a custom OpenSSL binary using the `MDB_OPENSSL` environment variable (e.g., `export MDB_OPENSSL=/path/to/openssl`).
  You normally want to use this system binary e.g., `/usr/bin/openssl` but things like `spack` environment sometimes
  install `openssl` which takes precedence over the system installation.

## Dependencies

### Non-Python Dependencies

* Either `gdb` or `lldb` (depending on your preference)

`mdb` does not package `gdb` or `lldb`. You will need these installed on your system in order to run `mdb`. Please visit
the debugger's respective sites for installation instructions e.g., [`gdb`](https://sourceware.org/gdb/) and
[`lldb`](https://lldb.llvm.org/resources/build.html).

### Python Dependencies

The main python dependencies are listed in the [`pyproject.toml`](pyproject.toml) file, e.g.,

* `python>=3.10`
* `click`
* `matplotlib`
* `numpy`
* `pexpect`

These will all be installed as part of the default `pip` installation. See [installing
mdb](https://mdb.readthedocs.io/en/latest/installation.html#installing-mdb) in the documentation for more information.

* `termgraph` (optional - fancy Unicode plots straight to your terminal)

`termgraph` is optional but can be installed alongside `mbd`. See [installing
mdb](https://mdb.readthedocs.io/en/latest/installation.html#installing-mdb) in the documentation for more information.

# Supported MPI implementations

Currently I am building and testing for open MPI only. In principle it really won't take much work to expand to other
implementations but I just haven't done it yet.

- [x] Open MPI
- [x] cray MPI
- [x] mpich (due to a bug in mpich `mdb` only supports `>=4.3.2` - see
  [#65](https://github.com/TomMelt/mdb/issues/65) for more info)
- [ ] Intel oneapi MPI (currently working with Intel on bug)
- [ ] Slurm `srun` (should work but still needs testing)
- [ ] others...

# TODO

- [ ] print aggregated backtrace (holistic metric)
- [ ] record asciinema demo? / youtube video?

# Contributing

If you would like to be involved in the development, feel free to submit a PR. A word of caution though... the code is currently
in a highly volatile state and a plan major changes to the interface and layout. I will update this section when I reach a more
stable part of the development. Either way changes are welcome at anytime.

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for more details on how best to contribute.

# Developers

For development it is best to install `mdb` with some additional dependencies. These can be installed following the [installing
mdb for developers](https://mdb.readthedocs.io/en/latest/installation.html#for-developers) guide.

# Acknowledgements

This project was inspired by [@mystery-e204](https://github.com/mystery-e204)'s [mpidb](https://github.com/mystery-e204/mpidb)
tool and [@Azrael3000](https://github.com/Azrael3000)'s [tmpi](https://github.com/Azrael3000/tmpi) tmux interface.

# Similar Projects

I have recently come across [@robertu94](https://github.com/robertu94)'s [mpigdb](https://github.com/robertu94/mpigdb). It
seems to offer similar functionality
and it has a closer integration with gdb using gdb's inbuilt `inferior`s to handle multiple processes at the same time (see
[gdb manual sec. 4.9](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Inferiors-Connections-and-Programs.html#Inferiors-Connections-and-Programs)
for more info). The main difference from my perspective is that I can plot variables across MPI processes using `mdb` and AFAIK
`mpigdb` cannot. If you like `mdb` you may want to check out `mpigdb` as well.
