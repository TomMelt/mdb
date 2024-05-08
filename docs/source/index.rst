.. Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
   details.

mdb
===

Welcome to ``mdb``'s documentation! ``mdb`` is a debugger aimed at parallel programs using the `MPI
<https://www.mpi-forum.org>`_ programming paradigm. ``mdb`` acts as a wrapper around different
serial debugger backends e.g.,  `gdb <https://sourceware.org/gdb>`_ and `lldb
<https://lldb.llvm.org/>`_. It supports the following languages:

* C
* C++
* Fortran

.. toctree::
   :maxdepth: 2
   :caption: Getting Started:

   Installation <installation>
   Quick Start <quick-start>

.. toctree::
   :maxdepth: 2
   :caption: Reference:
   :hidden:

   mdb Command Line Interface (CLI) <mdb-cli>
   gdb Cheat Sheet <gdbcheatsheet>
   Environment Variables <environment-vars>
   Client-Server Interface <client-server>

.. toctree::
   :maxdepth: 2
   :caption: API:
   :hidden:

   mdb API <mdb>

.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
