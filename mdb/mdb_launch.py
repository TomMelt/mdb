import subprocess as sub
import os
import click
import sys


@click.command()
@click.option("-p", "--port", default=2000, help="Starting port address. Each rank's port is assigned as [port_address + rank].")
@click.option("--args", help="program and args for gdb")
def launch(port, args):
    prog_opts = dict(port=port, args=args)

    try:
        prog_opts["no_ranks"] = int(os.environ["OMPI_COMM_WORLD_SIZE"])
        prog_opts["my_rank"] = int(os.environ["OMPI_COMM_WORLD_RANK"])
    except KeyError as e:
        print(e)
        exit(1)
    launch_server(**prog_opts)


def launch_server(my_rank, no_ranks, port, args):
    print(f"no of ranks = {no_ranks} , my rank = {my_rank}.")
    port = port + int(my_rank)
    sub.run(["gdbserver", f"localhost:{port}", f"{args}"])
    print(f"server on rank {my_rank} closed")
    return
