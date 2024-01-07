.. Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
   details.

.. _quick_start:

Quick Start
===========

The ``mdb`` program has two subcommands which act as modes of operation, ``launch`` and ``attach``.
``mdb``'s command line interface (CLI) is built with `Click
<https://click.palletsprojects.com/en/8.1.x/>`_ and each command has a ``--help`` option. For more
information please see the :ref:`cli` documentation. For example, ``mdb attach --help`` produces the
following output.

.. code-block:: console

    $ mdb attach --help
    Usage: mdb attach [OPTIONS]

    Options:
      -n, --ranks INTEGER         Total number of ranks to debug.  [default: 1]
      -s, --select TEXT           Rank(s) to debug e.g., 0,3-5 will debug ranks
                                  0,3,4 and 5. If empty all ranks will be
                                  selected. Note ranks starts with zero index.
      -h, --host TEXT             Host machine name.  [default: localhost]
      -p, --port INTEGER          Starting port address. Each rank's port is
                                  assigned as [port_address + rank].  [default:
                                  2000]
      -b, --breakpt TEXT          By default mdb will search for the first
                                  breakpoint (main or MAIN__). You can chose to
                                  override this by manually specifying a specific
                                  breakpoint.  [default: main]
      -x, --exec-script FILENAME  Execute a set of mdb commands contained in a
                                  script file.
      --plot-lib TEXT             Plotting library to use. Recommended default is
                                  [uplot] but if this is not available
                                  [matplotlib] will be used. [matplotlib] is best
                                  if there are many ranks to debug e.g., -s 0-100.
                                  [default: uplot]
      --help                      Show this message and exit.


Launching the mdb Client
------------------------

To begin a debugging session, first we must launch the debugger as part of the MPI launcher.
Currently supported MPI launchers are intel MPI and open MPI ``mpirun`` and slurm's ``srun``. For
simplicity, this example will all be run on the same machine

Here is an example launching ``mdb`` binary called ``a.out`` on 4 processes.

.. code-block:: console

   $ mpirun -n 4 mdb launch a.out
   Process /home/melt/sync/cambridge/projects/side/meltdb-old/a.out created; pid = 163542
   Listening on port 2002
   Process /home/melt/sync/cambridge/projects/side/meltdb-old/a.out created; pid = 163548
   Listening on port 2001
   Process /home/melt/sync/cambridge/projects/side/meltdb-old/a.out created; pid = 163550
   Listening on port 2000
   Process /home/melt/sync/cambridge/projects/side/meltdb-old/a.out created; pid = 163554
   Listening on port 2003

Now in a separate terminal (but same machine)

..
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

