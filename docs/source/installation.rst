.. Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
   details.

.. _installation:

Installing mdb
==============

Windows Support
---------------

**Please Note**: ``mdb`` does not run on Windows. This is due to a core dependency ``pexpect`` which
does not currently support windows for the ``pexpect.spawn`` and ``pexpect.run`` methods (see `here
<https://pexpect.readthedocs.io/en/stable/overview.html#pexpect-on-windows>`_ for more information).

Standard Installation (UNIX)
----------------------------

The easiest way to install ``mdb`` is to clone the repo and install it into a `conda environment
<https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_, or
other virtual environment of your choice.

First we will create and activate a ``conda`` environment for ``mdb`` (you can optionally specify a
``python`` version e.g., using ``python==3.12.0``).

.. code-block:: console

   $ conda create -n mdb python
   $ conda activate mdb

Then we can download and install the ``mdb`` code. You can download/clone the ``mdb`` code anywhere
but in this example I will choose the home directory.

.. code-block:: console

   $ cd ~
   $ git clone https://github.com/TomMelt/mdb.git
   $ cd mdb
   $ pip install -e .

That's it! We now have ``mdb`` installed and ready to go. You can test the install was successfully
by running ``mdb --help``. You should see the following output.

.. code-block:: console

   $ mdb --help
   Usage: mdb [OPTIONS] COMMAND [ARGS]...

   Options:
     --help  Show this message and exit.

     Commands:
       attach
       launch

For Developers
--------------

If you plan to carry out development it will be handy to install some additional dependencies. This
can be done in the following way.

.. code-block:: console

   $ pip install -e .[docs,develop]

``docs`` installs packages required to build the documentation and ``develop`` installs packages
required for verifying the quality of the code. Please also familiarize yourself with the
`CONTRIBUTING.md <https://github.com/TomMelt/mdb/blob/main/CONTRIBUTING.md>`_ guide, for more
details on how to best contribute to ``mdb``.

The additional ``develop`` dependencies are, ``black``, ``flake8`` and ``mypy``.

* `black <https://black.readthedocs.io/en/stable>`_ is used for formatting the source code.
* `flake8 <https://flake8.pycqa.org/en/latest>`_ is used to check the style and quality of some
  python code.
* `mypy <https://mypy.readthedocs.io/en/stable>`_ is a static type checker and is used to help
  ensure that variables and functions are being used correctly.
