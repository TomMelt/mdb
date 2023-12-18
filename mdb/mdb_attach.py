import signal

import click

from .mdb_client import Client
from .mdb_shell import mdbShell


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
    default="",
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
@click.option("--program", help="program for gdb to debug.", required=True)
def attach(ranks, select, host, port, program):
    # debug all ranks if "select" is not set
    if select == "":
        select = ",".join([str(rank) for rank in list(range(ranks))])

    prog_opts = dict(ranks=ranks, select=select, host=host, port=port, program=program)

    client = Client(prog_opts)
    client.connect()
    signal.signal(signal.SIGINT, client.close_procs)
    mshell = mdbShell(prog_opts, client)
    mshell.cmdloop()
