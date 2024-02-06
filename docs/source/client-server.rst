.. Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
   details.

.. _client_server:

Client-Server Interface
=======================

Due to security limitation of ``gdb`` (see `gdb manual
<https://sourceware.org/gdb/current/onlinedocs/gdb.html/Server.html>`_) ``mdb`` implements its own
client-server interface. This section explains the plan for this interface.

Launch Mode
-----------

The first stage of debugging with ``mdb`` is to run the ``launch`` command. ``mdb launch`` is the
part that actually runs the target binary using the MPI launcher (``mpirun``, ``mpiexec``, ``srun`` etc.).

#. ``mdb launch`` starts two child processes; (a) the first process runs the MPI launcher, in this
   example ``mpirun``, and (b) the second is an ``mdb exchange server`` which will be responsible
   for authenticating communication between the ``gdb`` subprocesses and the ``mdb attach`` process.
#. The call to ``mpirun`` in the previous step will launch ``nproc`` ``mdb server`` processes which will
   provide a thin wrapper around ``gdb``, essentially providing encrypted command input and output
   to each rank.
#. ``mdb exchange server`` will perform a TLS handshake with each ``mdb server`` process. This
   sets up the initial encrypted communication channel.
#. The last step in launch mode is for each ``mdb server`` process to communicate some basic
   information with the ``mdb exchange server``, such as, IP address (or ``HOSTNAME``), port number
   and MPI rank.

.. image:: figs/client-server-schematic-launch.svg

Attach Mode
-----------

Now that the debug processes are launched we can connect using the ``mdb attach`` command.

#. Running ``mdb attach`` will trigger a TLS handshake with the ``mdb exchange server`` on the
   specified host (``--host [hostname]``).
#. Once authenticated, ``mdb`` can forward command IO to and from the ``mdb exchange server``.
#. ``mdb server`` has already authenticated the connection with thin ``mdb server`` processes. It
   forwards the relevant commands to each rank.
#. Each rank responds depending on the command issued.
#. ``mdb exchange server`` sends encrypted output back to ``mdb attach``, where it will be
   unencrypted automatically using TLS/SSL sockets.

.. image:: figs/client-server-schematic-attach.svg

Communication Protocol
----------------------

This is still a work in progress but some things are already certain:

* messages will be sent as ``json``.
* each message will include a version number.
* each message will have a destination (e.g., ``exchange server`` or ``mdb server``).
