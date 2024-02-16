# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import asyncio
import logging
import shlex

import click
from typing_extensions import TypedDict

from .debug_client import DebugClient
from .exchange_server import AsyncExchangeServer
from .mdb_server import Server

Server_opts = TypedDict(
    "Server_opts",
    {
        "ranks": int,
        "select": str,
        "hostname": str,
        "launch_command": str,
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
    "--launch-command",
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
    required=True,
    nargs=-1,
)
def launch(
    ranks: int,
    select: str | None,
    hostname: str,
    launch_command: str,
    port: int,
    config_filename: str,
    auto_restart: bool,
    args: tuple[str] | list[str],
) -> None:
    """Launch mdb debug server.

    Example:

    $ mdb launch -n 8 --auto-restart ./simple-mpi.exe
    """

    logging.basicConfig(
        filename="mdb-launch.log", encoding="utf-8", level=logging.DEBUG
    )

    args = list(args)

    # debug all ranks if "select" is not set
    if select is None:
        select = f"0-{ranks - 1}"

    opts = {
        "hostname": hostname,
        "port": port,
    }
    server = AsyncExchangeServer(opts=opts)
    task = server.start_server()

    loop = asyncio.get_event_loop()
    loop.create_task(task)

    proc = asyncio.create_subprocess_exec(*shlex.split("mpirun --app .mdb.conf"))

    loop.create_task(proc)

    print("something else")

    # for rank in range(1, 16):
    #     opts = {
    #         "exchange_hostname": "localhost",
    #         "exchange_port": 2000,
    #         "rank": rank,
    #         "backend": "gdb",
    #         "target": "examples/simple-mpi.exe",
    #         "args": "",
    #     }
    #     dbg_client = DebugClient(opts)
    #     loop.create_task(dbg_client.run())
    loop.run_forever()

    # server_opts: Server_opts = dict(
    #     ranks=ranks,
    #     select=select,
    #     hostname=hostname,
    #     launch_command=launch_command,
    #     port=port,
    #     config_filename=config_filename,
    #     args=" ".join(args),
    # )

    # server = Server(server_opts)
    # server.write_app_file()
    # keep_running = True
    # while keep_running:
    #     server.run()
    #     if not auto_restart:
    #         keep_running = False
    # return
