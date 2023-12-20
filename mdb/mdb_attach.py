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
@click.option(
    "-b",
    "--breakpt",
    default="",
    show_default=True,
    help="By default mdb will search for the first breakpoint (main or MAIN__). You can chose to override this by manually specifying a specific breakpoint.",
)
@click.option(
    "--plot-lib",
    default="uplot",
    show_default=True,
    help="Plotting library to use. Recommended default is [uplot] but if this is not available [matplotlib] will be used. [matplotlib] is best if there are many ranks to debug e.g., -s 0-100.",
)
def attach(ranks, select, host, port, program, breakpt, plot_lib):
    # debug all ranks if "select" is not set
    if select == "":
        select = ",".join([str(rank) for rank in list(range(ranks))])

    supported_plot_libs = ["uplot", "matplotlib"]
    if plot_lib not in supported_plot_libs:
        msg = f"warning: unrecognized plot library [{plot_lib}]. Supported libraries are [{supported_plot_libs}]."
        raise ValueError(msg)

    prog_opts = dict(
        ranks=ranks,
        select=select,
        host=host,
        port=port,
        program=program,
        breakpt=breakpt,
        plot_lib=plot_lib,
    )

    client = Client(prog_opts)
    client.connect()
    signal.signal(signal.SIGINT, client.close_procs)
    mshell = mdbShell(prog_opts, client)
    mshell.cmdloop()
