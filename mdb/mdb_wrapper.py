# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import asyncio

import click
from typing_extensions import TypedDict

from .debug_client import DebugClient

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
    "-m",
    "--my-rank",
    required=True,
    help="Rank of this debug process.",
)
@click.option(
    "-h",
    "--exchange-hostname",
    required="localhost",
    help="Hostname where exchange server is running.",
)
@click.option(
    "-p",
    "--exchange-port",
    required=True,
    help="Port address of exchange server.",
)
@click.option(
    "-b",
    "--back-end",
    required=True,
    help="Debug backend e.g., gdb, lldb etc.",
)
@click.option(
    "-t",
    "--target",
    type=click.File("r"),
    required=True,
    help="Target binary to debug.",
)
@click.argument(
    "args",
    required=False,
    nargs=-1,
)
def wrapper(
    my_rank: int,
    exchange_hostname: str,
    exchange_port: int,
    back_end: str,
    target: click.File,
    args: tuple[str] | list[str],
) -> None:
    """Run mdb wrapper for debug backend.

    Note: this is not expected to be run manually by the user. It should be
    called by mdb launch which will pass the appropriate options.

    Example:

    $ mdb wrapper -m 1 -h localhost -p 2000 -b gdb -t simple-example.exe [ARGS]"
    """

    args = list(args)

    print("target = \n", target.name)

    opts = {
        "exchange_hostname": exchange_hostname,
        "exchange_port": exchange_port,
        "rank": my_rank,
        "backend": back_end,
        "target": target.name,
        "args": args,
    }
    dbg_client = DebugClient(opts)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(dbg_client.run())
    loop.close()
