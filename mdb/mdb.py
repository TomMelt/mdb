import click
from .mdb_attach import attach
from .mdb_launch import launch


@click.group()
def main():
    pass


main.add_command(attach)
main.add_command(launch)
