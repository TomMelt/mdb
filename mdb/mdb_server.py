# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

from __future__ import annotations

import logging
import shlex
import subprocess as sub
from typing import TYPE_CHECKING

from .utils import parse_ranks

if TYPE_CHECKING:
    from .mdb_launch import Server_opts



class WrapperLauncher:

    def __init__(self, prog_opts: Server_opts) -> None:
        self.mpi_mode: str = ""
        self.ranks: int = prog_opts["ranks"]
        self.hostname: str = prog_opts["hostname"]
        self.mpi_command: str = prog_opts["mpi_command"]
        self.select: set[int] = parse_ranks(prog_opts["select"])
        self.config_filename: str = prog_opts["config_filename"]
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
        for i in range(self.ranks):
            if i in self.select:
                line = f"-n 1 mdb wrapper -m {rank} -h {self.hostname} -p {self.port} -b {self.backend} -t {self.target} {self.args}"
            else:
                line = f"-n 1 {self.target} {self.args}"
            lines.append(line)

        with open(self.config_filename, "w") as appfile:
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
        config_filename = self.config_filename
        launcher = self.launch_command
        command = 
        if self.mpi_mode == "intel":
            f"{launcher} --configfile {config_filename}"
        elif self.mpi_mode == "open mpi":
            sub.run(shlex.split(f"{launcher} --app {config_filename}"))
        else:
            logging.error("error: MPI mode not supported.")
            exit(1)
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
