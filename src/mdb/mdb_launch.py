# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import asyncio
import logging
import os
import shlex
import signal
import socket
from asyncio import Task
from os import mkdir
from os.path import exists, expanduser, join
from socket import gethostbyaddr
from subprocess import run

import click
from typing_extensions import TypedDict

from .exchange_server import AsyncExchangeServer
from .mdb_wrapper import Wrapper_opts, WrapperLauncher

Server_opts = TypedDict(
    "Server_opts",
    {
        "ranks": int,
        "select": str,
        "hostname": str,
        "mpi_command": str,
        "port": int,
        "appfile": str,
        "args": str,
    },
)


@click.command()
@click.option(
    "-n",
    "--ranks",
    default=1,
    show_default=True,
    help="Total number of ranks to debug.",
)
@click.option(
    "-s",
    "--select",
    default=None,
    show_default=True,
    help="Rank(s) to debug e.g., 0,3-5 will debug ranks 0,3,4 and 5. If empty all ranks will be selected. Note ranks starts with zero index.",
)
@click.option(
    "-h",
    "--hostname",
    default="",
    show_default=True,
    help="Hostname of machine where exchange server will run. If left empty, it will default to the IP address of the machine that submits the mdb launch command. Note that if running multinode jobs the hostname needs to be resolvable and not just localhost i.e., 127.0.0.1.",
)
@click.option(
    "--mpi-command",
    default="mpirun",
    show_default=True,
    help="MPI launcher e.g., mpirun, mpiexec, srun etc.",
)
@click.option(
    "--mpi-config-opt",
    default="",
    show_default=True,
    help="mdb will try to automatically detect the option name for the --app/--configfile option. This option overrides the automatic detection.",
)
@click.option(
    "-p",
    "--port",
    default=2000,
    show_default=True,
    help="Starting port address. Each rank's port is assigned as [port_address + rank].",
)
@click.option(
    "-b",
    "--backend",
    default="gdb",
    help="Debug backend e.g., gdb, lldb etc.",
)
@click.option(
    "-t",
    "--target",
    type=click.File("r"),
    required=True,
    help="Target binary to debug.",
)
@click.option(
    "--mdb-home",
    default="~/.mdb",
    show_default=True,
    help="Directory where mdb SSL/TLS certificate and key are stored.",
)
@click.option(
    "--redirect-stdout",
    type=click.File("w"),
    required=False,
    help="Redirect stdout from the target binary. If omitted, stdout will not be redirected.",
)
@click.option(
    "-r",
    "--auto-restart",
    is_flag=True,
    default=False,
    show_default=True,
    help="Allow mdb launcher to automatically relaunch the job if the debug session ends.",
)
@click.option(
    "--log-level",
    default="WARN",
    show_default=True,
    help="Choose minimum level of debug messages: [DEBUG, INFO, WARN, ERROR, CRITICAL]",
)
@click.option(
    "--connection-attempts",
    default=10,
    show_default=True,
    help="Maximum number of failed connection attempts. A connection attempt is made once per second.",
)
@click.argument(
    "args",
    required=False,
    nargs=-1,
)
def launch(
    ranks: int,
    select: str | None,
    hostname: str,
    mpi_command: str,
    mpi_config_opt: str,
    port: int,
    backend: str,
    target: click.File,
    redirect_stdout: click.File,
    auto_restart: bool,
    log_level: str,
    mdb_home: str,
    connection_attempts: int,
    args: tuple[str] | list[str],
) -> None:
    """Launch mdb debug server.

    Example:

    $ mdb launch -n 8 -b gdb -t ./simple-mpi.exe -- -arg1 value
    """

    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: %s" % log_level)

    logging.basicConfig(encoding="utf-8", level=numeric_level)
    logger = logging.getLogger(__name__)

    MDB_HOME = expanduser(mdb_home)
    MDB_CERT_PATH = join(MDB_HOME, "cert.pem")
    MDB_KEY_PATH = join(MDB_HOME, "key.rsa")

    if not exists(MDB_HOME):
        mkdir(MDB_HOME)

    # certificate hostname cannot be an IP address so it must be resolved to a hostname
    if hostname == "":
        hostname = socket.gethostbyname(socket.gethostname())
    print(f"running on host: {hostname}")
    print("to connect to the debugger run:")
    print(f"mdb attach -h {hostname} -p {port}\n")
    cert_host = gethostbyaddr(hostname)[0]
    subj = f"/C=XX/ST=mdb/L=mdb/O=mdb/OU=mdb/CN={cert_host}"
    opts = "req -x509 -newkey rsa:4096 -sha256 -days 365"

    # Use MDB_OPENSSL environment variable if set, otherwise default to 'openssl'
    openssl_cmd = os.environ.get("MDB_OPENSSL", "openssl")
    cmd = f'{openssl_cmd} {opts} -keyout {MDB_KEY_PATH} -out {MDB_CERT_PATH} -nodes -subj "{subj}"'
    proc = run(shlex.split(cmd), capture_output=True)
    logger.debug("generating ssl certificate and key")
    logger.debug(cmd)
    logger.debug(proc.stderr.decode())

    # Check if certificate generation was successful
    if proc.returncode != 0:
        raise RuntimeError(
            "Failed to generate SSL certificate.\n"
            "You can try setting a custom OpenSSL path: export MDB_OPENSSL=/path/to/openssl"
        )

    # Verify that the certificate files were created
    if not exists(MDB_CERT_PATH) or not exists(MDB_KEY_PATH):
        raise FileNotFoundError(
            "SSL certificate files were not created. "
            f"Expected files: {MDB_CERT_PATH} and {MDB_KEY_PATH}\n"
            "Please check that OpenSSL is working correctly. "
            "You can try: export MDB_OPENSSL=/path/to/openssl"
        )

    args = list(args)

    # debug all ranks if "select" is not set
    if select is None:
        select = f"0-{ranks - 1}"

    wl_opts: Wrapper_opts = {
        "appfile": ".mdb.appfile",
        "args": " ".join(args),
        "backend": backend,
        "hostname": hostname,
        "mpi_command": mpi_command,
        "mpi_config_opt": mpi_config_opt,
        "port": port,
        "ranks": ranks,
        "select": select,
        "connection_attempts": connection_attempts,
        "target": target.name,
        "redirect_stdout": (
            redirect_stdout.name if redirect_stdout is not None else None
        ),
    }

    wrapper_launcher = WrapperLauncher(wl_opts)
    wrapper_launcher.write_app_file()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    cmd = wrapper_launcher.launch_command()
    logger.debug(f"launch command: {cmd}")
    launch_task = loop.create_task(asyncio.create_subprocess_exec(*shlex.split(cmd)))

    exchange_opts = {
        "hostname": hostname,
        "port": port,
        "number_of_ranks": ranks,
        "backend": backend,
        "launch_task": launch_task,
        "select": select,
    }
    server = AsyncExchangeServer(opts=exchange_opts)
    loop.create_task(server.start_server())

    for s in [signal.SIGINT, signal.SIGTERM]:

        def shutdown_func() -> Task[None]:
            return asyncio.create_task(server.shutdown(s.name))

        loop.add_signal_handler(s, shutdown_func)

    loop.run_forever()
