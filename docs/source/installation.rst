.. Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
   details.

.. _installation:

Installing mdb
==============

**Please Note**: ``mdb`` does not run on Windows. This is due to a core dependency ``pexpect`` which
does not currently support windows for the ``pexpect.spawn`` and ``pexpect.run`` methods (see `here
<https://pexpect.readthedocs.io/en/stable/overview.html#pexpect-on-windows>`_ for more information).

The easiest way to install ``mdb`` is to clone the repo and install it into a `conda environment
<https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_.

First we will create and activate a conda environment for ``mdb`` (you can optionally specify a
``python`` version using ``python==3.12.0``).

.. code-block:: console

   $ conda create -n mdb python
   $ conda activate mdb

Then we can download and install the ``mdb`` code. You can download/clone the ``mdb`` code anywhere
but in this example I will choose the home directiory.

.. code-block:: console

   $ cd ~
   $ git clone https://github.com/TomMelt/mdb.git
   $ cd mdb
   $ pip install -e .

That's it! We now have ``mdb`` installed and ready to go. You can test the install was successfuly
by running ``mdb --help``. You should see the following output.

.. code-block:: console

   $ mdb --help
   Usage: mdb [OPTIONS] COMMAND [ARGS]...

   Options:
     --help  Show this message and exit.

     Commands:
       attach
       launch
