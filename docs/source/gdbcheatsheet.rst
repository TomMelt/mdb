.. Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
   details.

.. _gdbcheat:

gdb Cheat Sheet
===============

The following commands may be helpful when using ``mdb``. All of these can be passed to ``gdb``
using the command ``command [gdb command]`` (or optionally specify which ranks to run the command on
with ``command [ranks] [gdb command]``). A full list of ``gdb`` commands can be found in `gdb's
manual <https://sourceware.org/gdb/current/onlinedocs/gdb.html>`_. Any valid ``gdb`` command can be
used in ``mdb`` (as long as it runs in remote execution mode -- but that's nearly all the useful
ones I can think of). The main exceptions are ``start`` and ``run`` but ``mdb`` launches binary
already and will stop at ``main`` by default. You can manually specify the breakpoint if this is not
suitable (see :ref:`quick_start` for more info).

+-------------+--------------------------+-------------------------+-----------+
| Command     | Effect                   | Example                 | Aliases   |
+=============+==========================+=========================+===========+
| backtrace   | print backtrace          | command 1-4 backtrace   | bt        |
+-------------+--------------------------+-------------------------+-----------+
| continue    | continue running program | command continue        | c         |
+-------------+--------------------------+-------------------------+-----------+
|             |                          |                         |           |
+-------------+--------------------------+-------------------------+-----------+
|             |                          |                         |           |
+-------------+--------------------------+-------------------------+-----------+
|             |                          |                         |           |
+-------------+--------------------------+-------------------------+-----------+
