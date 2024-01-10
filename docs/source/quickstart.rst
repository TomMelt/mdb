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
                                  breakpoint (`main` or `MAIN__`). You can chose
                                  to override this by manually specifying a
                                  specific breakpoint.  [default: main]
      -x, --exec-script FILENAME  Execute a set of mdb commands contained in a
                                  script file.
      --plot-lib TEXT             Plotting library to use. Recommended default is
                                  [uplot] but if this is not available
                                  [matplotlib] will be used. [matplotlib] is best
                                  if there are many ranks to debug e.g., -n 100.
                                  [default: uplot]
      --help                      Show this message and exit.


An example program
------------------

Well, first things first, we need a program to debug. Whilst you probably already have one if you
are looking for an MPI debugger, it may be best to start simple. To that end, I have provided a
simple example program written in ``fortran``. We will need to move into the ``examples/``
directory and compile the code.

.. code-block:: console

   $ cd examples/
   $ make
   mpif90 -ggdb -c  simple-mpi.f90 -o simple-mpi.o
   mpif90  simple-mpi.o -o simple-mpi.exe
   $ ls
   Makefile  README.md  simple-mpi.exe  simple-mpi.f90  simple-mpi.o  simple-mpi-script.mdb

You should now see the binary ``simple-mpi.exe``. I also included a simple debug script
``simple-mpi-script.mdb`` which can be used to execute a sample debug session, but we will come to
that later.

Launching the mdb Client
------------------------

To begin a debugging session, first we must launch the debugger as part of the MPI launcher.
Currently supported MPI launchers are Intel MPI and open MPI ``mpirun`` and Slurm's ``srun``. For
simplicity, this example will all be run on the same machine

Here is an example launching ``mdb`` with the ``simple-mpi.exe`` binary on 8 processes. If you don't
have an 8 core processor to hand, then you can pass the ``--oversubscribe`` option to open MPI's
``mpirun``. Intel's ``mpirun`` can oversubscribe by default, but for this tutorial I am running (and
compiling) with open MPI (and ``gfortran``).

.. code-block:: console

   $ mpirun -n 8 mdb launch ./simple-mpi.exe 
   Process ./simple-mpi.exe created; pid = 62872
   Listening on port 2006
   Process ./simple-mpi.exe created; pid = 62876
   Listening on port 2002
   Process ./simple-mpi.exe created; pid = 62881
   Listening on port 2003
   Process ./simple-mpi.exe created; pid = 62887
   Listening on port 2004
   Process ./simple-mpi.exe created; pid = 62891
   Listening on port 2005
   Process ./simple-mpi.exe created; pid = 62896
   Listening on port 2000
   Process ./simple-mpi.exe created; pid = 62901
   Listening on port 2007
   Process ./simple-mpi.exe created; pid = 62906
   Listening on port 2001

Attaching to the mdb Client
---------------------------

Now in a separate terminal (but same physical machine -- remote debugging is still WIP) run the
``attach`` command. We are over-riding the default ``main`` breakpoint (which generally works for
C/C++ programs) with ``MAIN__`` using the ``-b/--breakpt`` option. The reason for this is that the
entry point for Fortran programs tends to be different from the standard ``main`` entry point for
C/C++ programs. It's worth noting, you can choose any other valid breakpoint as an initial starting
point e.g., ``simple-mpi.f90:10`` for a breakpoint on line ``10`` in file ``simple-mpi.f90``. For
now we will continue with this.

.. code-block:: console

   $ mdb attach -n 8 -b MAIN__
   Connecting processes... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 8/8

The first part of the output will look something like the above. This means that ``mdb`` has
successfully attached to the client processes (launched in the previous step). If you get a
``TimeOutError`` like the following, then please check ``mdb`` was launched properly in the first
step.

.. code-block:: console

   Connecting processes... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0/8
   error: mdb timeout with error message "localhost:2000: Connection timed out."

If connection was successful, then the connection output will be followed by the welcome text.

.. code-block:: console

   mdb - mpi debugger - built on gdb. Type ? for more info. To exit interactive mode type "Ctrl+]"

This text provides information on how to use ``mdb``. Typing ``help`` or ``?`` will print this same
message. Typing ``help`` or ``?`` followed by one of the ``mdb`` commands will display help text for
that command e.g.,

.. code-block:: console

   (mdb 0-7) ? info

        Description:
        Print basic statistics (min, mean, max) and produce a bar chart for a
        given variable [var] on all selected processes. This is intended for
        float/integer variables.

        Example:
        The following command will print variable [var] on all selected processes.

            (mdb) pprint [var]

Another important point is the ``mdb`` prompt ``(mdb 0-7)``, in this specific example. This tells us
that any commands issued via ``command`` will be sent to processors ``0-7``. For example,

.. code-block:: console

   (mdb 0-7) command info proc
   1:      process 62906
   1:      cmdline = './simple-mpi.exe'
   1:      cwd = '/home/melt/mdb/examples'
   1:      exe = '/home/melt/mdb/examples/simple-mpi.exe'

   7:      process 62901
   7:      cmdline = './simple-mpi.exe'
   7:      cwd = '/home/melt/mdb/examples'
   7:      exe = '/home/melt/mdb/examples/simple-mpi.exe'

   ...

   0:      process 62896
   0:      cmdline = './simple-mpi.exe'
   0:      cwd = '/home/melt/mdb/examples'
   0:      exe = '/home/melt/mdb/examples/simple-mpi.exe'

From brevity I have used ``...`` to shorten the output. ``command`` is used to send commands
directly to the ``gdb`` instance of each processor. In this case I sent ``info proc`` which prints
information on each process. Notice that the process id's match those from the ``launch`` command.
Whilst there is no guarantee for the order of output, each process will have it's process rank id
prepended to the output in the format ``[rank id]:`` . If you want to issue a ``gdb`` command to a
specific rank (or set of ranks) only then you can provide an optional set of ranks, either
comma-separated, hyphen-separated or a mix of both. For example, to send command ``backtrace -1`` to
ranks ``0,2-4`` use the following.

.. code-block:: console

   (mdb 0-7) command 0,2-4 backtrace -1
   2:      #0  simple () at simple-mpi.f90:1

   3:      #0  simple () at simple-mpi.f90:1

   4:      #0  simple () at simple-mpi.f90:1

   0:      #0  simple () at simple-mpi.f90:1

In theory you now have enough information to start debugging your own programs. Have a play with
this simple example if you want to get to grips with ``mdb``. There are a couple more useful things
I want to show you though before you leave.

Interactive mode
----------------

My main focus for ``mdb`` was to leverage ``gdb`` as much as possible i.e., as to not reinvent the
wheel. Each process is simply connected to a gdb instance. Therefore you can connect to any specific
rank and dive straight into ``gdb`` - if you want. To do this, we will use the ``interact`` command.
Specifically we are going to connect to rank 1's ``gdb`` instance.

.. code-block:: console

   (mdb 0-7) interact 1
   (gdb)

Notice that the command prompt has now changed from ``(mdb 0-7)`` to ``(gdb)``. This represents that
we are now inside ``gdb``. **To exit** interactive mode (not ``gdb``) we can type ``CTRL+]``. If you
type ``q`` or ``quit`` from inside of ``gdb`` it will kill that processes instance of ``gdb`` and
the rest of the processes may also break. In the interactive session we can issue any *gdbserver
compatible* commands (see :ref:`supported`), for example,

.. code-block:: console

   (gdb) show version
   GNU gdb (Ubuntu 12.1-0ubuntu1~22.04) 12.1
   Copyright (C) 2022 Free Software Foundation, Inc.
   License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>

   ...

   For help, type "help".
   Type "apropos word" to search for commands related to "word".


Upon pressing ``CTRL+]`` control will return back to ``mdb`` and you should see the prompt change
back to ``(mdb 0-7)``.

Plotting variables across ranks
-------------------------------

It may be useful for some applications to see how the value of a single variable varies across all
ranks. This can be achieved with the ``info`` command, which will display an ASCII plot (if
``youplot`` is installed) or a ``Matplotlib`` plot if not. In ``simple-example.f90`` we can see that
variable ``var`` is set on line 15.

.. code-block:: fortran

   11   call mpi_init(ierror)
   12   call mpi_comm_size(mpi_comm_world, size_of_cluster, ierror)
   13   call mpi_comm_rank(mpi_comm_world, process_rank, ierror)
   14 
   15   var = 10.*process_rank
   16 
   17   if (process_rank == 0) then
   18     print *, 'process 0 sleeping for 3s...'

We will set the following breakpoints:

.. code-block:: console

   (mdb 0-7) command b simple-mpi.f90:15
   (mdb 0-7) command b simple-mpi.f90:17
   (mdb 0-7) command continue
   (mdb 0-7) command 0-2,5,7 continue

The first breakpoint ``b simple-mpi.f90:15`` will ensure we make it past the call to ``mpi_init``.
The second breakpoint ``b simple-mpi.f90:17`` is just the other side of where ``var`` is set. The
first continue command will be sent to all ranks ``0-7``. This will get all ranks up to the first
breakpoint. The second continue command ``command 0-2,5,7 continue`` will only move ranks
``0,1,2,5`` and ``7`` to line ``17``. If we issue the ``info var`` command we should see a plot
showing non-zero values for those ranks (except rank ``0`` which is actually set to ``0.0``.)

.. code-block:: console

   (mdb 0-7) info var
   min : 0.0
   max : 70.0
   mean: 18.75
   n   : 8
             ┌                                        ┐
           0 ┤ 0.0
           1 ┤■■■■■ 10.0
           2 ┤■■■■■■■■■■ 20.0
      rank 3 ┤ 0.0
           4 ┤ 0.0
           5 ┤■■■■■■■■■■■■■■■■■■■■■■■■ 50.0
           6 ┤ 0.0
           7 ┤■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■ 70.0
             └                                        ┘
                                var

We can see that ranks ``0,1,2,5`` and ``7`` are displaying the correct values. If we now continue on
ranks ``3,4`` and ``6`` we should see the full plot.

.. code-block:: console

   (mdb 0-7) command 3,4,6 c
   (mdb 0-7) info var
   min : 0.0
   max : 70.0
   mean: 35.0
   n   : 8
             ┌                                        ┐
           0 ┤ 0.0
           1 ┤■■■■■ 10.0
           2 ┤■■■■■■■■■■ 20.0
      rank 3 ┤■■■■■■■■■■■■■■■ 30.0
           4 ┤■■■■■■■■■■■■■■■■■■■ 40.0
           5 ┤■■■■■■■■■■■■■■■■■■■■■■■■ 50.0
           6 ┤■■■■■■■■■■■■■■■■■■■■■■■■■■■■■ 60.0
           7 ┤■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■ 70.0
             └                                        ┘
                                var

Perfect, we can now see that all ranks are showing the expected values. For debugging large numbers
of ranks e.g., n>10, it is probably best to switch to ``matplotlib`` using the ``mdb attach
--plot-lib matplotlib`` command.

Exiting mdb
-----------

To quit the ``mdb`` debugger, you can either press ``CTRL+D`` or type ``quit``. **Note** ``CTRL+C``
is forwarded directly to each ``gdb`` processes allowing the user to interrupt execution as would be
expected in a serial ``gdb`` session.

Scripting the mdb Debug Session
-------------------------------

All of the commands explained here have been placed into an example script ``simple-mpi-script.mdb``
which can be used to execute this debug session. The script is selected via the
``-x/--exec-script`` option. Feel free to use this as inspiration for scripting your own debug
sessions. To run the example debug session you can use the following command,

.. code-block:: console

   $ mdb attach -n 8 -b MAIN__ -x simple-mpi-script.mdb


Scripted debugging is also allowed in ``gdb`` and this is where the true benefit of CLI tools really
shines.
