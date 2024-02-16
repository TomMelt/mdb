# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import asyncio
import logging
import signal

import click
from typing_extensions import TypedDict

from .async_client import mdbClient
from .mdb_client import Client
from .mdb_shell import mdbShell

Prog_opts = TypedDict(
    "Prog_opts",
    {
        "ranks": int,
        "select": str,
        "host": str,
        "port": int,
        "breakpt": str,
        "exec_script": str,
        "plot_lib": str,
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
    "-p",
    "--port",
    default=2000,
    show_default=True,
    help="Starting port address. Each rank's port is assigned as [port_address + rank].",
)
@click.option(
    "-b",
    "--breakpt",
    default="main",
    show_default=True,
    help="By default mdb will set ``main`` as the first breakpoint. You can chose to override this by manually specifying a specific breakpoint.",
)
@click.option(
    "-x",
    "--exec-script",
    type=click.File("r"),
    help="Execute a set of mdb commands contained in a script file.",
)
@click.option(
    "--plot-lib",
    default="termgraph",
    show_default=True,
    help="Plotting library to use. Recommended default is [termgraph] but if this is not available [matplotlib] will be used. [matplotlib] is best if there are many ranks to debug e.g., -n 100.",
)
def attach(
    ranks: int,
    select: str | None,
    host: str,
    port: int,
    breakpt: str,
    exec_script: click.File,
    plot_lib: str,
) -> None:
    """Attach to mdb debug server.

    Example:

    $ mdb attach -n 8
    """

    logging.basicConfig(
        filename="mdb-attach.log", encoding="utf-8", level=logging.DEBUG
    )

    # debug all ranks if "select" is not set
    if select is None:
        select = f"0-{ranks - 1}"

    supported_plot_libs = ["termgraph", "matplotlib"]
    if plot_lib not in supported_plot_libs:
        msg = f"warning: unrecognized plot library [{plot_lib}]. Supported libraries are [{supported_plot_libs}]."
        raise ValueError(msg)

    if exec_script is None:
        script = None
    else:
        script = exec_script.name

    client_opts = {
        "exchange_hostname": "localhost",
        "exchange_port": 2000,
        "backend": "gdb",
    }
    client = mdbClient(opts=client_opts)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.run())
    loop.close()

    # prog_opts: Prog_opts = dict(
    #     ranks=ranks,
    #     select=select,
    #     host=host,
    #     port=port,
    #     breakpt=breakpt,
    #     exec_script=script,
    #     plot_lib=plot_lib,
    # )

    # client = Client(prog_opts)
    # try:
    #     client.connect()
    # except TimeoutError as e:
    #     print(f'error: mdb timeout with error message "{e}"')
    #     exit(1)
    # mshell = mdbShell(prog_opts, client)
    # signal.signal(signal.SIGINT, mshell.hook_SIGINT)
    # mshell.cmdloop()
