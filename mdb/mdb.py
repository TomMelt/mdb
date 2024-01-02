# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import click

from .mdb_attach import attach
from .mdb_launch import launch


@click.group()
def main() -> None:
    pass


main.add_command(attach)
main.add_command(launch)
