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

   Usage: mdb attach [OPTIONS]

     Attach to mdb debug server.

     Example:

     $ mdb attach -x script.mdb

   Options:
     -h, --hostname TEXT         Hostname where exchange server is running.
                                 [default: localhost]
     -p, --port INTEGER          Starting port address. Each rank's port is
                                 assigned as [port_address + rank].  [default:
                                 2000]
     -s, --select TEXT           Rank(s) to debug e.g., 0,3-5 will debug ranks
                                 0,3,4 and 5. If empty all ranks will be
                                 selected. Note ranks starts with zero index.
     -x, --exec-script FILENAME  Execute a set of mdb commands contained in a
                                 script file.
     --log-level TEXT            Choose minimum level of debug messages: [DEBUG,
                                 INFO, WARN, ERROR, CRITICAL]  [default: WARN]
     --plot-lib TEXT             Plotting library to use. Recommended default is
                                 [termgraph] but if this is not available
                                 [matplotlib] will be used. [matplotlib] is best
                                 if there are many ranks to debug e.g., -n 100.
                                 [default: termgraph]
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
Currently supported MPI launchers are Intel MPI and open MPI ``mpirun``. For simplicity, this
example will all be run on the same machine

Here is an example launching ``mdb`` with the ``simple-mpi.exe`` binary on 8 processes. If you don't
have an 8 core processor to hand, then you can pass the ``--oversubscribe`` option to open MPI's
``mpirun`` using ``--mpi-command "mpirun --oversubscribe"``. Intel's ``mpirun`` can oversubscribe by
default, but for this tutorial I am running (and compiling) with open MPI (and ``gfortran``). By
default the log level of ``mdb launch`` is set to ``WARN``. For the tutorial we will override this
to show more information using the ``--log-level`` flag.

.. code-block:: console

   $ mdb launch -b gdb -n 8 -t ./simple-mpi.exe --log-level=DEBUG
   DEBUG:asyncio:Using selector: EpollSelector
   DEBUG:mdb.mdb_launch:launch command: mpirun --app .mdb.appfile
   INFO:mdb.exchange_server:echange server started :: localhost:2000
   DEBUG:mdb.async_connection:msg received [debug_conn_request]
   INFO:mdb.exchange_server:exchange server received {debug_conn_request} from {debug client}.
   DEBUG:mdb.async_connection:sent message [mdb_conn_response]
   DEBUG:mdb.async_connection:msg received [debug_conn_request]
   INFO:mdb.exchange_server:exchange server received {debug_conn_request} from {debug client}.
   DEBUG:mdb.async_connection:sent message [mdb_conn_response]
   DEBUG:mdb.async_connection:msg received [debug_conn_request]
   INFO:mdb.exchange_server:exchange server received {debug_conn_request} from {debug client}.
   DEBUG:mdb.async_connection:sent message [mdb_conn_response]
   DEBUG:mdb.async_connection:msg received [debug_conn_request]
   INFO:mdb.exchange_server:exchange server received {debug_conn_request} from {debug client}.
   DEBUG:mdb.async_connection:sent message [mdb_conn_response]
   DEBUG:mdb.async_connection:msg received [debug_conn_request]
   INFO:mdb.exchange_server:exchange server received {debug_conn_request} from {debug client}.
   DEBUG:mdb.async_connection:sent message [mdb_conn_response]
   DEBUG:mdb.async_connection:msg received [debug_conn_request]
   INFO:mdb.exchange_server:exchange server received {debug_conn_request} from {debug client}.
   DEBUG:mdb.async_connection:sent message [mdb_conn_response]
   DEBUG:mdb.async_connection:msg received [debug_conn_request]
   INFO:mdb.exchange_server:exchange server received {debug_conn_request} from {debug client}.
   DEBUG:mdb.async_connection:sent message [mdb_conn_response]
   DEBUG:mdb.async_connection:msg received [debug_conn_request]
   INFO:mdb.exchange_server:exchange server received {debug_conn_request} from {debug client}.
   DEBUG:mdb.async_connection:sent message [mdb_conn_response]

.. _attach_client:

Attaching to the mdb Client
---------------------------

Now in a separate terminal (but same physical machine -- see :ref:`remote_debugging` for information
on how to attach to remote machines) run the ``attach`` command.

.. code-block:: console

   $ mdb attach --log-level=DEBUG
   mdb - mpi debugger - built on various backends. Type ? for more info. To exit interactive mode
   type "q", "quit", "Ctrl+D" or "Ctrl+]".
   (mdb 0-7)

The first part of the output will look something like the above. This means that ``mdb`` has
successfully attached to the client processes (launched in the previous step). If you get a
connection error like the following, then please check ``mdb`` was launched properly in the first
step.

.. code-block:: console

   $ mdb attach --log-level=DEBUG
   couldn't connect to exchange server at localhost:2000.

Hopefully you are now connected and you see the following welcome message.

.. code-block:: console

   mdb - mpi debugger - built on gdb. Type ? for more info. To exit interactive mode type "q",
   "quit", "Ctrl+D" or "Ctrl+]".

This text provides information on how to use ``mdb``. Typing ``help`` or ``?`` will print this same
message. Typing ``help`` or ``?`` followed by one of the ``mdb`` commands will display help text for
that command e.g.,

.. code-block:: console

   (mdb 0-7) ? command

        Description:
        Run [command] on every selected process. Alternatively, manually
        specify which ranks to run the command on.

        Example:
        The following command will run {self.backend.name} command [command] on every process.

            (mdb) command [command]

        The following command will run {self.backend.name} command [command] on processes 0,3,4 and 5.

            (mdb) command 0,3-5 [command]


Another important point is the ``mdb`` prompt ``(mdb 0-7)``, in this specific example. This tells us
that any commands issued via ``command`` will be sent to processors ``0-7``. For example,

.. code-block:: console

   (mdb 0-7) command info proc
   0:      process 54584
   0:      cmdline = '/home/melt/sync/cambridge/projects/side/mdb/examples/simple-mpi.exe'
   0:      cwd = '/home/melt/sync/cambridge/projects/side/mdb'
   0:      exe = '/home/melt/sync/cambridge/projects/side/mdb/examples/simple-mpi.exe'
   ************************************************************************
   1:      process 54576
   1:      cmdline = '/home/melt/sync/cambridge/projects/side/mdb/examples/simple-mpi.exe'
   1:      cwd = '/home/melt/sync/cambridge/projects/side/mdb'
   1:      exe = '/home/melt/sync/cambridge/projects/side/mdb/examples/simple-mpi.exe'
   ************************************************************************
   .
   .
   .
   ************************************************************************
   7:      process 54590
   7:      cmdline = '/home/melt/sync/cambridge/projects/side/mdb/examples/simple-mpi.exe'
   7:      cwd = '/home/melt/sync/cambridge/projects/side/mdb'
   7:      exe = '/home/melt/sync/cambridge/projects/side/mdb/examples/simple-mpi.exe'

From brevity I have used ``...`` to shorten the output. ``command`` is used to send commands
directly to the ``gdb`` instance of each processor (see :ref:`broadcast_mode` which covers the
``broadcast`` command -- this is useful for longer debug sessions). In this case I sent ``info
proc`` which prints information on each process. The output is sorted in numerical order with each
process having it's own rank id prepended to the output in the format ``[rank id]:``. Each rank's
output is separated by a dividing line of asterisk characters i.e., ``***``. If you want to issue a
``gdb`` command to a specific rank (or set of ranks) only then you can provide an optional set of
ranks, either comma-separated, hyphen-separated or a mix of both. For example, to send command
``backtrace -1`` to ranks ``0,2-4`` use the following.

.. code-block:: console

   (mdb 0-7) command 0,2-4 backtrace -1
   0:      #0  simple () at simple-mpi.f90:8
   ************************************************************************
   2:      #0  simple () at simple-mpi.f90:8
   ************************************************************************
   3:      #0  simple () at simple-mpi.f90:8
   ************************************************************************
   4:      #0  simple () at simple-mpi.f90:8

In theory you now have enough information to start debugging your own programs. Have a play with
this simple example if you want to get to grips with ``mdb``. There are a couple more useful things
I want to show you though before you leave.

.. _broadcast_mode:

Broadcast mode
--------------

Whilst the ``command`` command is pretty useful. For long debugging sessions it can be annoying
constantly prefixing ``command`` to every ``gdb`` command you want to run. This is where broadcast
mode comes in handy. In broadcast mode all commands will be automatically prefixed with ``command``
so that they run on the selected ranks. By default all ranks are selected unless you have manually
specified a different selection with the ``select`` command.

To enter broadcast mode type the following,

.. code-block:: console

   (mdb 0-7) broadcast start
   (bcm 0-7)

The command prompt will turn to ``(bcm 0-7)`` and will also change color to yellow (depending on
your terminal color scheme). To leave broadcast mode either press ``CTRL+D`` or type
``quit``/``broadcast stop``, e.g.,

.. code-block:: console

   (bcm 0-7) broadcast stop
   (mdb 0-7)

The prompt should return to ``(mdb 0-7)`` and be back to the standard font color.

Plotting variables across ranks
-------------------------------

It may be useful for some applications to see how the value of a single variable varies across all
ranks. This can be achieved with the ``plot`` command, which will display an ASCII plot (if
``termgraph`` is installed) or a ``Matplotlib`` plot if not. In ``simple-example.f90`` we can see
that variable ``var`` is set on line 15.

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
``0,1,2,5`` and ``7`` to line ``17``. If we issue the ``plot var`` command we should see a plot
showing non-zero values for those ranks (except rank ``0`` which is actually set to ``0.0``.)

.. code-block:: console

   (mdb 0-7) plot var
   min  =  0.0
   max  =  70.0
   mean =  18.75

   0:  0.00
   1: ▇▇▇▇▇▇▇ 10.00
   2: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 20.00
   3:  0.00
   4:  0.00
   5: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 50.00
   6:  0.00
   7: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 70.00

We can see that ranks ``0,1,2,5`` and ``7`` are displaying the correct values. If we now continue on
ranks ``3,4`` and ``6`` we should see the full plot.

.. code-block:: console

   (mdb 0-7) command 3,4,6 c
   (mdb 0-7) plot var
   min  =  0.0
   max  =  70.0
   mean =  35.0

   0:  0.00
   1: ▇▇▇▇▇▇▇ 10.00
   2: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 20.00
   3: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 30.00
   4: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 40.00
   5: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 50.00
   6: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 60.00
   7: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 70.00

Perfect, we can now see that all ranks are showing the expected values. For debugging large numbers
of ranks e.g., n>10, it is probably best to switch to ``matplotlib`` using the ``mdb attach
--plot-lib matplotlib`` command.

Exiting mdb
-----------

To quit the ``mdb`` debugger, you can either press ``CTRL+D`` or type ``quit``.

.. note::
   ``CTRL+C`` is forwarded directly to each ``gdb`` processes allowing the user to interrupt
   execution as would be expected in a serial ``gdb`` session.

Scripting the mdb Debug Session
-------------------------------

All of the commands explained here have been placed into an example script ``simple-mpi-script.mdb``
which can be used to execute this debug session. The script is selected via the
``-x/--exec-script`` option. Feel free to use this as inspiration for scripting your own debug
sessions. To run the example debug session you can use the following command,

.. code-block:: console

   $ mdb attach -x simple-mpi-script.mdb --log-level=DEBUG

Scripted debugging is also allowed in ``gdb`` and this is where the true benefit of CLI tools really
shines.

.. _remote_debugging:

Remote debugging
----------------

This section (and :ref:`attach_client`) needs to be updated now that the client-server backend has
been rewritten.
