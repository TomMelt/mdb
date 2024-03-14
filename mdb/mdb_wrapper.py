# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import asyncio
import logging
import subprocess

import click
from typing_extensions import TypedDict

from .debug_client import DebugClient
from .utils import parse_ranks

Server_opts = TypedDict(
    "Server_opts",
    {
        "ranks": int,
        "select": str,
        "host": str,
        "launch_command": str,
        "port": int,
        "appfile": str,
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
    "--backend",
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
    backend: str,
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
        "backend": backend,
        "target": target.name,
        "args": args,
    }

    # configure the global logger
    logging.basicConfig(filename=f"rank.{my_rank}.log", level=logging.DEBUG)

    dbg_client = DebugClient(opts)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(dbg_client.run())
    loop.close()


class WrapperLauncher:
    def __init__(self, prog_opts: Server_opts) -> None:
        self.mpi_mode: str = ""
        self.ranks: int = prog_opts["ranks"]
        self.hostname: str = prog_opts["hostname"]
        self.port: str = prog_opts["port"]
        self.target: str = prog_opts["target"]
        self.mpi_command: str = prog_opts["mpi_command"]
        self.select: set[int] = parse_ranks(prog_opts["select"])
        self.appfile: str = prog_opts["appfile"]
        self.backend: str = prog_opts["backend"]
        self.args: str = prog_opts["args"]
        self.set_mpi_mode()
        return

    def write_app_file(self) -> None:
        """Generate an app file for mpi launcher.

        Returns:
            None
        """

        lines = []
        for rank in range(self.ranks):
            if rank in self.select:
                line = f"-n 1 mdb wrapper -m {rank} -h {self.hostname} -p {self.port} -b {self.backend} -t {self.target} {self.args}"
            else:
                line = f"-n 1 {self.target} {self.args}"
            lines.append(line)

        with open(self.appfile, "w") as appfile:
            appfile.write("\n".join(lines))

        return

    def launch_command(self) -> str:
        """run a gdb server on the current rank.

        Args:
            rank: rank on which gdb server is running.
            start_port: starting port. Port number will be port+rank. Defaults to 2000.
            args: binary to debug and optional list of arguments for that binary.

        Returns:
            None
        """
        appfile = self.appfile
        launcher = self.mpi_command
        if self.mpi_mode == "intel":
            return f"{launcher} --configfile {appfile}"
        elif self.mpi_mode == "open mpi":
            return f"{launcher} --app {appfile}"
        else:
            logging.error("error: MPI mode not supported.")
            exit(1)
        return

    def set_mpi_mode(self) -> None:
        """Set mpi_mode depending on which mpirun implementation is being used."""

        supported_modes = ["intel", "open mpi"]

        mpi_version = subprocess.run(
            ["mpirun", "--version"], capture_output=True
        ).stdout.decode("utf8")

        for name in supported_modes:
            if name in mpi_version.lower():
                self.mpi_mode = name
                return
        self.mpi_mode = "unsupported"
        return
