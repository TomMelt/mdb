.. Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
   details.

mdb environment variables
=========================

SSL/TLS Debugging
-----------------

``mdb`` uses SSL/TLS to encrypt the TCP communication between the clients and the exchange server.
See the :ref:`client_server` documentation for more information.

This can make debugging harder as the messages are encrypted. This can be disabled by setting the
following environment variable.

.. code-block:: console

   export MDB_DISABLE_HOSTNAME_VERIFY=1

.. warning::
   Do not use ``MDB_DISABLE_HOSTNAME_VERIFY`` on a multi-user system, such as a shared HPC cluster. This
   is for local debugging only.

Custom OpenSSL Path
-------------------

By default, ``mdb`` uses the ``openssl`` command found in the system PATH. If you need to use a
specific OpenSSL installation, you can set the ``MDB_OPENSSL`` environment variable to point to the
desired OpenSSL binary.

.. code-block:: console

   export MDB_OPENSSL=/path/to/custom/openssl

This is useful when if you have multiple OpenSSL versions installed (this is a common issue when
using ``spack`` environments).

If ``MDB_OPENSSL`` is not set, ``mdb`` will default to using the ``openssl`` command from the system PATH.

.. _cli_env_vars:

CLI options as environment variables
------------------------------------

Thanks to the ``click`` CLI, ``mdb`` supports setting options as environment variables instead of
passing them as command line arguments. For example, the following two commands are equivalent. They
both launch ``mdb`` with a ``log_level`` of ``DEBUG``.

.. code-block:: console

   mdb launch --log-level=DEBUG -b gdb -t examples/simple-mpi.exe -n 8
   MDB_LAUNCH_LOG_LEVEL=DEBUG mdb launch b gdb -t examples/simple-mpi.exe -n 8

The syntax for using an environment variable is ``MDB_X_Y`` where ``X`` is the subcommand
(``LAUNCH`` or ``ATTACH``) and ``Y`` is the option name.

.. note::
   If the option has hyphens they will be replaced wih underscores for the environment variable
   name. E.g., ``--log-level`` becomes ``LOG_LEVEL``.

If the user specifies a CLI option and the corresponding environment variable, the CLI option takes
precedence.

.. code-block:: console

   MDB_LAUNCH_LOG_LEVEL=DEBUG mdb launch --log-level=WARN b gdb -t examples/simple-mpi.exe -n 8

In the example above, the log level will be set to ``WARN``. The environment variable
``MDB_LAUNCH_LOG_LEVEL=DEBUG`` is ignored.
