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
mpirun -n 8 mdb launch --args ./a.out
```

In a separate terminal (and even separate machine if you wish (but you'd need to use SSH)) use `mdb` in attach mode.

```bash
mdb attach -n 8 -s 0,2-4 --program a.out
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

1. Clone the repository.

    ```bash
    git clone https://github.com/TomMelt/mdb.git
    ```

2. (optional - but recommended) Create a conda environment or venv.

    ```bash
    conda create -n mdb-new python
    conda activate mdb-new
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

# Acknowledgements

This project was inspired by @mystery-e204's [mpidb](https://github.com/mystery-e204/mpidb) tool and @Azrael3000's
[tmpi](https://github.com/Azrael3000/tmpi) tmux interface.

# Similar Projects

I have recently come across @robertu94's [mpigdb](https://github.com/robertu94/mpigdb). I wish I came across it before I started
my own because I think it handles the interface to gdb in a nicer way and sort of does what I wanted. The main difference from
my perspective is that I can plot variables across mpi processes using `mdb` and AFAIK `mpigdb` cannot. If you like `mdb` I
recommend checking out `mpigdb` as well -- it also uses rust!
