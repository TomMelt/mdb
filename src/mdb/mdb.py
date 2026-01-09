# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import click
from importlib import metadata

from .mdb_attach import attach
from .mdb_launch import launch
from .mdb_wrapper import wrapper


@click.group()
def main() -> None:
    """mdb is comprised of two sub-commands [attach] and [launch].

    They both need to be run in order to start a debug session.

    * Firstly, use the launch command to start the mdb debug processes.

    * Then, use attach to connect mdb to the debug processes.

    See documentation of the respective subcommands for more information.
    """
    pass


def run_main() -> None:
    """Wrapper around main function to add click environment variable support

    See [here](https://click.palletsprojects.com/en/8.1.x/options/#values-from-environment-variables) for more info.
    """
    main(auto_envvar_prefix="MDB")
    pass


@click.command()
def version() -> None:
    """Get the version number of mdb."""
    try:
        print(metadata.version("mdb-debugger"))
    except metadata.PackageNotFoundError:
        print("mdb-debugger not installed")


main.add_command(attach)
main.add_command(launch)
main.add_command(version)
main.add_command(wrapper)
