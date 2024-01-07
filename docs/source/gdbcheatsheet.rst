.. Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
   details.

gdb Cheat Sheet
===============

.. _supported:
Note on Supported Commands
--------------------------

Any valid ``gdb`` command can be used in ``mdb`` (as long as it runs in remote execution mode -- but
that's nearly all the useful ones I can think of). The main exceptions are ``start`` and ``run`` and
these wouldn't work in MPI mode anyway because you cannot (as far as I know) restart and MPI
application from within the process.

``mdb`` launches the binary to stop at ``main`` by default, which can optionally overridden to any
other valid breakpoint if this is not suitable (see :ref:`quick_start` for more info). Therefore
instead of using ``start`` or ``run`` commands, as you can non-MPI applications, ``mdb`` will
already be waiting at the breakpoint specified by ``-b/--breakpt``.

.. _gdbcheat:
Useful Commands
---------------

This section is a WIP and will be updated shortly.

The following commands may be helpful when using ``mdb``. All of these can be passed to ``gdb``
using the command ``command [gdb command]`` (or optionally specify which ranks to run the command on
with ``command [ranks] [gdb command]``). A full list of ``gdb`` commands can be found in `gdb's
manual <https://sourceware.org/gdb/current/onlinedocs/gdb.html>`_.

+-------------+--------------------------+-------------------------+-----------+
| Command     | Effect                   | Example                 | Aliases   |
+=============+==========================+=========================+===========+
| backtrace   | print backtrace          | command 1-4 backtrace   | bt        |
+-------------+--------------------------+-------------------------+-----------+
| continue    | continue running program | command continue        | c         |
+-------------+--------------------------+-------------------------+-----------+

