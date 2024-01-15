# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import click

from .mdb_attach import attach
from .mdb_launch import launch


@click.group()
def main() -> None:
    """mdb is comprised of two sub-commands [attach] and [launch].

    They both need to be run in order to start a debug session.

    * Firstly, use the launch command to start the mdb debug processes.
    * Then, use attach to connect mdb to the debug processes.

    See documentation of the respective subcommands for more information.
    """
    pass


main.add_command(attach)
main.add_command(launch)
