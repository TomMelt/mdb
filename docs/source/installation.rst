.. Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
   details.

.. _installation:

Installing mdb
==============

Windows Support
---------------

.. note::
   ``mdb`` does not run on Windows. This is due to a core dependency ``pexpect`` which does not
   currently support windows for the ``pexpect.spawn`` and ``pexpect.run`` methods (see `here
   <https://pexpect.readthedocs.io/en/stable/overview.html#pexpect-on-windows>`_ for more
   information).

Standard Installation (UNIX)
----------------------------

The easiest way to install ``mdb`` is to clone the repo and install it into a virtual environment of
your choice. For the following example, I will use Python's built-in `venv
<https://docs.python.org/3/library/venv.html>`_ virtual environment module.

First we will create and activate a virtual environment for ``mdb``.

.. code-block:: console

   $ python3 -m venv .mdb
   $ source .mdb/bin/activate

You then have two options for install. Either from GitHub source (recommended for developers) or using PyPI
(recommended for developers).

pip install
+++++++++++

To install ``mdb`` with the optional package ``termgraph`` use the following command (**Note:** the
name ``mdb`` is already in use on PyPI, so I have decided to call the repo ``mdb-debugger``)

.. code-block:: console

   $ pip install mdb-debugger[termgraph]

GitHub install
++++++++++++++

Then we can download and install the ``mdb`` code. You can download/clone the ``mdb`` code anywhere
but in this example I will choose the home directory.

.. code-block:: console

   $ cd ~
   $ git clone https://github.com/TomMelt/mdb.git
   $ cd mdb
   $ pip install .[termgraph]

That's it! We now have ``mdb`` installed and ready to go. You can test the install was successfully
by running ``mdb --help``. You should see the following output. Specifying ``[termgraph]`` is
optional but it will give pretty plots straight to the terminal.

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

   $ pip install -e .[docs,develop,termgraph]

The ``-e`` (or ``--editable``) flag installs the project in editable mode meaning that your changes
will be reflected when you save the source files and restart ``mdb``. ``docs`` installs packages
required to build the documentation and ``develop`` installs packages required for verifying the
quality of the code. Please also familiarize yourself with the `CONTRIBUTING.md
<https://github.com/TomMelt/mdb/blob/main/CONTRIBUTING.md>`_ guide, for more details on how to best
contribute to ``mdb``.

The additional ``develop`` dependencies are;

* `black <https://black.readthedocs.io/en/stable>`_ is used for formatting the source code.
* `flake8 <https://flake8.pycqa.org/en/latest>`_ is used to check the style and quality of some
  python code.
* `mypy <https://mypy.readthedocs.io/en/stable>`_ is a static type checker and is used to help
  ensure that variables and functions are being used correctly.
* `pytest <https://docs.pytest.org/en/7.4.x/>`_ for creating and running unit and integration tests
* `pytest-cov <https://pytest-cov.readthedocs.io/en/latest/index.html>`_ for producing coverage
  reports.
