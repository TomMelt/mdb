# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

from __future__ import annotations

import shlex
import subprocess as sub
from typing import TYPE_CHECKING

from .utils import parse_ranks

if TYPE_CHECKING:
    from .mdb_launch import Server_opts

_supported_modes = ["intel", "open mpi"]


class Server:
    mpi_mode: str = "unsupported"

    def __init__(self, prog_opts: Server_opts) -> None:
        self.ranks: int = prog_opts["ranks"]
        self.host: str = prog_opts["host"]
        self.launch_command: str = prog_opts["launch_command"]
        self.start_port: int = prog_opts["port"]
        self.select: set[int] = parse_ranks(prog_opts["select"])
        self.config_filename: str = prog_opts["config_filename"]
        self.args: str = prog_opts["args"]
        self.set_mpi_mode()
        return

    def write_app_file(self) -> None:
        """Generate an app file for mpi launcher.

        Returns:
            None
        """

        lines = []
        host = self.host
        start_port = self.start_port
        args = self.args
        for i in range(self.ranks):
            if i in self.select:
                line = f"-n 1 gdbserver {host}:{start_port + i} {args}"
            else:
                line = f"-n 1 {args}"
            lines.append(line)

        with open(self.config_filename, "w") as appfile:
            appfile.write("\n".join(lines))

        return

    def run(self) -> None:
        """run a gdb server on the current rank.

        Args:
            rank: rank on which gdb server is running.
            start_port: starting port. Port number will be port+rank. Defaults to 2000.
            args: binary to debug and optional list of arguments for that binary.

        Returns:
            None
        """
        print("Server is running...")
        config_filename = self.config_filename
        launcher = self.launch_command
        if self.mpi_mode == "intel":
            sub.run(shlex.split(f"{launcher} --configfile {config_filename}"))
        elif self.mpi_mode == "open mpi":
            sub.run(shlex.split(f"{launcher} --app {config_filename}"))
        else:
            print("error: MPI mode not supported.")
            exit(1)
        print("Server is closing...")
        return

    def set_mpi_mode(self) -> None:
        """Set mpi_mode depending on which mpirun implementation is being used."""

        mpi_version = sub.run(
            ["mpirun", "--version"], capture_output=True
        ).stdout.decode("utf8")

        for name in _supported_modes:
            if name in mpi_version.lower():
                self.mpi_mode = name
                return
        self.mpi_mode = "unsupported"
        return
