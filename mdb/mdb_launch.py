# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import click
from typing_extensions import TypedDict

from .mdb_server import Server

Server_opts = TypedDict(
    "Server_opts",
    {
        "ranks": int,
        "select": str,
        "host": str,
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
    "--host",
    default="localhost",
    show_default=True,
    help="Host machine name.",
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
    host: str,
    launch_command: str,
    port: int,
    config_filename: str,
    auto_restart: bool,
    args: tuple[str] | list[str],
) -> None:
    args = list(args)

    # debug all ranks if "select" is not set
    if select is None:
        select = f"0-{ranks - 1}"

    server_opts: Server_opts = dict(
        ranks=ranks,
        select=select,
        host=host,
        launch_command=launch_command,
        port=port,
        config_filename=config_filename,
        args=" ".join(args),
    )

    server = Server(server_opts)
    server.write_app_file()
    keep_running = True
    while keep_running:
        server.run()
        if not auto_restart:
            keep_running = False
    return
