.. Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
   details.

mdb
===

Welcome to ``mdb``'s documentation! ``mdb`` is a debugger aimed at parallel programs using the `MPI
<https://www.mpi-forum.org>`_ programming paradigm. ``mdb`` acts as a wrapper around GNU's `gdb
<https://sourceware.org/gdb>`_ and, as such, it supports the following languages:

* C
* C++
* Fortran

Technically ``gdb`` supports other languages as well, but this is the intersection of languages that
MPI is implemented in and that I have had a chance to test.

.. toctree::
   :maxdepth: 2
   :caption: Basics:

   Installation <installation>
   Quick Start <quickstart>
   Example Debug Session <example>

.. toctree::
   :maxdepth: 2
   :caption: Reference:

   Command Line Interface <click>
   gdb Cheat Sheet <gdbcheatsheet>

.. toctree::
   :maxdepth: 2
   :caption: API:

   mdb API <mdb>

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
