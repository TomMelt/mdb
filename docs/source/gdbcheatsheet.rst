.. Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
   details.

gdb Cheat Sheet
===============

.. _supported:

Note on Supported Commands
--------------------------

Most valid ``gdb`` commands can be used in ``mdb`` (as long as they run in remote execution mode --
but that's nearly all the useful ones I can think of). The main exceptions are ``start`` and ``run``
and these wouldn't work in MPI mode anyway because you cannot (as far as I know) restart and MPI
application from within the process.

``mdb`` launches the binary to stop at ``main`` by default, which can optionally overridden to any
other valid breakpoint if this is not suitable (see :ref:`quick_start` for more info). Therefore
instead of using ``start`` or ``run`` commands, as you can non-MPI applications, ``mdb`` will
already be waiting at the breakpoint specified by ``-b/--breakpt``.

For MPI debugging ``gdb``'s reverse commands (e.g., ``reverse-next``, ``reverse-step`` etc.) are not
supported. Each ``gdb`` instance is not MPI-aware and you cannot step backwards through
``MPI_init()``, for example. If you want to "go backwards" you should restart the ``mdb`` debug
session.

.. _gdbcheat:

Useful Commands
---------------

The following commands may be helpful when using ``mdb``. All of these can be passed to ``gdb``
using the command ``command [gdb command]`` (or optionally specify which ranks to run the command on
with ``command [ranks] [gdb command]``). A full list of ``gdb`` commands can be found in `gdb's
manual <https://sourceware.org/gdb/current/onlinedocs/gdb.html>`_.

.. csv-table:: Moving through the program
   :header: Command , Action                     , Example                    , Aliases

   ``next``         , run to next line           , ``command n``              , ``n``
   ``step``         , step into function         , ``command s``              , ``s``
   ``backtrace``    , print backtrace            , ``command bt``             , ``bt`` and ``where``
   ``continue``     , continue running program   , ``command c``              , ``c``
   ``until``        , run until ``{expression}`` , ``command u {expression}`` , ``u``
   ``up``           , move up one frame          , ``command up``             , ``up``
   ``down``         , move down one frame        , ``command down``           , ``do``

.. csv-table:: Breakpoints and Watchpoints
   :header: Command    , Action               , Example                                 , Aliases

   ``breakpoint``      , set a breakpoint     , ``command b {expression}``              , ``b``
                       ,                      , ``command b [filename]:[line_no]``      ,
                       , (conditional)        , ``command b [func_name] if myrank < 2`` ,
   ``watchpoint``      , set a watchpoint     , ``command watch [variable_name]``       , ``watch``
                       , (on write)           , ``command watch foo``                   ,
                       , (on read)            , ``command rwatch foo``                  ,
                       , (on read-write)      , ``command awatch foo``                  ,
   ``delete [num]``    , delete breakpoint #2 , ``command del 2``                       , ``del``

.. csv-table:: Displaying Information
   :header: Command     , Action                                      , Example                 , Aliases

   ``print``            , print variable ``{var}``                    , ``command p {var}``     , ``p``
   ``display``          , show variable ``{var}`` after every command , ``command disp {var}``  , ``disp``
   ``info {option}``    , print information for:                      ,                         ,
                        , (breakpoints)                               , ``command info break``  , ``info b``
                        , (locals)                                    , ``command info locals`` , ``info loc``

.. csv-table:: Changing Execution
   :header: Command , Action                             , Example                           , Aliases

   ``set variable`` , change value of variable ``{var}`` , ``command set var {var}={value}`` , ``set var``

Single Key Mode (TUI)
---------------------

This can be used inside an interactive ``gdb`` session when the ``tui`` is activated. To enter
Single Key Mode press ``CTRL-x s``. To exit press ``q``. This allows you to use a single key press
to issue the following commands:

.. csv-table:: Single Key Mode
   :header: Key, Command

   ``c``, ``continue``
   ``d``, ``down``
   ``f``, ``finish``
   ``n``, ``next``
   ``o``, ``nexti`` (the letter "o" stands for "step [o]ver")
   ``r``, ``run``
   ``s``, ``step``
   ``i``, ``stepi`` (the letter "i" stands for "step [i]nto")
   ``u``, ``up``
   ``v``, ``info locals``
   ``w``, ``where``
   ``q``, (exit Single Key Mode)
