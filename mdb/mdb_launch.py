import os
import subprocess as sub

import click


@click.command()
@click.option(
    "-p",
    "--port",
    default=2000,
    show_default=True,
    help="Starting port address. Each rank's port is assigned as [port_address + rank].",
)
@click.argument(
    "args",
    # help="program and any command line arguments. Similar to gdb option.",
    required=True,
    nargs=-1,
)
def launch(port, args):
    args = list(args)
    prog_opts = dict(port=port, args=args)
    prog_opts["no_ranks"] = None
    prog_opts["my_rank"] = None

    env_vars = {
        "open MPI": ("OMPI_COMM_WORLD_SIZE", "OMPI_COMM_WORLD_RANK"),
        "intel MPI": ("MPI_LOCALNRANKS", "MPI_LOCALRANKID"),
        "PMI": ("PMI_SIZE", "PMI_RANK"),
        "slurm": ("SLURM_NTASKS", "SLURM_PROCID"),
    }

    for env_name, (env_size, env_rank) in env_vars.items():
        try:
            prog_opts["no_ranks"] = int(os.environ[env_size])
            prog_opts["my_rank"] = int(os.environ[env_rank])
        except KeyError:
            pass

    if prog_opts["no_ranks"] is None or prog_opts["my_rank"] is None:
        print(
            "Error: cannot find MPI information in environment variables. I currently search for:"
        )
        for env_name, env_var in env_vars.items():
            print(f"Library: {env_name} , variables {env_var}")
        exit(1)

    launch_server(**prog_opts)


def launch_server(my_rank, no_ranks, port, args):
    port = port + int(my_rank)
    sub.run(["gdbserver", f"localhost:{port}"] + args)
    print(f"server on rank {my_rank} closed")
    return
