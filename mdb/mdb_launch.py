# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import asyncio
import logging
import shlex

import click
from typing_extensions import TypedDict

from .exchange_server import AsyncExchangeServer
from .mdb_wrapper import WrapperLauncher

Server_opts = TypedDict(
    "Server_opts",
    {
        "ranks": int,
        "select": str,
        "hostname": str,
        "mpi_command": str,
        "port": int,
        "config_filename": str,
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
    default="localhost",
    show_default=True,
    help="Hostname machine name.",
)
@click.option(
    "--mpi-command",
    default="mpirun",
    show_default=True,
    help="MPI launcher e.g., mpirun, mpiexec, srun etc.",
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
    "--config-filename",
    default=".mdb.conf",
    show_default=True,
    help="filename for the mpirun configuration.",
)
@click.option(
    "-r",
    "--auto-restart",
    is_flag=True,
    default=False,
    show_default=True,
    help="Allow mdb launcher to automatically relaunch the job if the debug session ends.",
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
    port: int,
    backend: str,
    target: click.File,
    config_filename: str,
    auto_restart: bool,
    args: tuple[str] | list[str],
) -> None:
    """Launch mdb debug server.

    Example:

    $ mdb launch -n 8 --auto-restart ./simple-mpi.exe
    """

    logging.basicConfig(
        encoding="utf-8",
        level=logging.DEBUG,
    )
    logger = logging.getLogger(__name__)

    args = list(args)

    # debug all ranks if "select" is not set
    if select is None:
        select = f"0-{ranks - 1}"

    wl_opts = {
        "ranks": ranks,
        "select": select,
        "hostname": hostname,
        "backend": backend,
        "mpi_command": mpi_command,
        "target": target.name,
        "port": port,
        "config_filename": config_filename,
        "args": " ".join(args),
    }

    wrapper_launcher = WrapperLauncher(wl_opts)
    wrapper_launcher.write_app_file()

    exchange_opts = {
        "hostname": hostname,
        "port": port,
        "number_of_ranks": ranks,
        "backend": backend,
    }
    server = AsyncExchangeServer(opts=exchange_opts)

    loop = asyncio.get_event_loop()
    loop.create_task(server.start_server())

    cmd = "mpirun --app .mdb.conf"
    logger.debug("Spawning debugger instances: %s", cmd)
    loop.create_task(asyncio.create_subprocess_exec(*shlex.split(cmd)))

    loop.run_forever()

    keep_running = True
    while keep_running:
        server.run()
        if not auto_restart:
            keep_running = False
    return
