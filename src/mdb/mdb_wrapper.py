# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import asyncio
import logging
import subprocess
from enum import Enum

import click
from typing_extensions import TypedDict

from .debug_client import DebugClient
from .utils import parse_ranks

Wrapper_opts = TypedDict(
    "Wrapper_opts",
    {
        "appfile": str,
        "args": str,
        "backend": str,
        "hostname": str,
        "mpi_command": str,
        "mpi_config_opt": str,
        "port": int,
        "ranks": int,
        "select": str,
        "target": str,
        "redirect_stdout": str,
        "connection_attempts": int,
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
@click.option(
    "--redirect-stdout",
    type=click.File("w"),
    required=False,
    help="Redirect stdout from the target binary. If omitted, stdout will not be redirected.",
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
def wrapper(
    my_rank: int,
    exchange_hostname: str,
    exchange_port: int,
    backend: str,
    target: click.File,
    redirect_stdout: click.File,
    connection_attempts: int,
    args: tuple[str] | list[str],
) -> None:
    """Run mdb wrapper for debug backend.

    Note: this is not expected to be run manually by the user. It should be
    called by mdb launch which will pass the appropriate options.

    Example:

    $ mdb wrapper -m 1 -h localhost -p 2000 -b gdb -t simple-example.exe [ARGS]"
    """

    args = list(args)

    opts = {
        "exchange_hostname": exchange_hostname,
        "exchange_port": exchange_port,
        "rank": my_rank,
        "backend": backend,
        "target": target.name,
        "redirect_stdout": (
            redirect_stdout.name if redirect_stdout is not None else None
        ),
        "connection_attempts": connection_attempts,
        "args": args,
    }

    # configure the global logger
    logging.basicConfig(filename=f"rank.{my_rank}.log", level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    dbg_client = DebugClient(opts)  # type: ignore
    logger.debug("debug client initialized")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(dbg_client.run())
    loop.close()


class MPI_Mode(Enum):
    UNSUPPORTED = "unsupported"
    INTEL = "Intel"
    OPENMPI = "Open MPI"
    MPICH = "MPICH"


class WrapperLauncher:
    def __init__(self, prog_opts: Wrapper_opts) -> None:
        self.mpi_mode: MPI_Mode = MPI_Mode.UNSUPPORTED
        self.ranks = prog_opts["ranks"]
        self.hostname = prog_opts["hostname"]
        self.port = prog_opts["port"]
        self.target = prog_opts["target"]
        self.redirect_stdout = prog_opts["redirect_stdout"]
        self.mpi_command = prog_opts["mpi_command"]
        self.mpi_config_opt = prog_opts["mpi_config_opt"]
        self.select = parse_ranks(prog_opts["select"])
        self.appfile = prog_opts["appfile"]
        self.backend = prog_opts["backend"]
        self.connection_attempts = prog_opts["connection_attempts"]
        self.args = prog_opts["args"]
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
                options = [
                    "-n",
                    "1",
                    "mdb",
                    "wrapper",
                    "-m",
                    f"{rank}",
                    "-h",
                    f"{self.hostname}",
                    "-p",
                    f"{self.port}",
                    "-b",
                    f"{self.backend}",
                    "-t",
                    f"{self.target}",
                    "--connection-attempts",
                    f"{self.connection_attempts}",
                ]
                if self.redirect_stdout is not None:
                    options = options + [
                        "--redirect-stdout",
                        f"{self.redirect_stdout}",
                    ]
                options = options + [
                    "--",
                    f"{self.args}",
                ]
                line = " ".join(options)
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
        if self.mpi_config_opt != "":
            return f"{launcher} --{self.mpi_config_opt} {appfile}"
        if self.mpi_mode == MPI_Mode.INTEL:
            return f"{launcher} --configfile {appfile}"
        elif self.mpi_mode == MPI_Mode.OPENMPI:
            return f"{launcher} --app {appfile}"
        elif self.mpi_mode == MPI_Mode.MPICH:
            return f"{launcher} --pmi-port --configfile {appfile}"
        else:
            logging.error(
                "error: MPI mode not supported. Try specifying the --configfile option."
            )
            exit(1)

    def set_mpi_mode(self) -> None:
        """Set mpi_mode depending on which mpirun implementation is being used."""

        supported_modes = {
            MPI_Mode.INTEL: "intel",
            MPI_Mode.OPENMPI: "open mpi",
            MPI_Mode.MPICH: "hydra",
        }

        mpi_version = subprocess.run(
            ["mpirun", "--version"], capture_output=True
        ).stdout.decode("utf8")

        for mode, search_key in supported_modes.items():
            if search_key in mpi_version.lower():
                self.mpi_mode = mode
                return
        self.mpi_mode = MPI_Mode.UNSUPPORTED
        return
