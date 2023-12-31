# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

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
def launch(port: int, args: tuple[str] | list[str]) -> None:
    args = list(args)
    num_ranks = 0
    rank = 0

    env_vars = {
        "open MPI": ("OMPI_COMM_WORLD_SIZE", "OMPI_COMM_WORLD_RANK"),
        "intel MPI": ("MPI_LOCALNRANKS", "MPI_LOCALRANKID"),
        "PMI": ("PMI_SIZE", "PMI_RANK"),
        "slurm": ("SLURM_NTASKS", "SLURM_PROCID"),
    }

    for env_name, (env_size, env_rank) in env_vars.items():
        try:
            num_ranks = int(os.environ[env_size])
            rank = int(os.environ[env_rank])
        except KeyError:
            pass

    if num_ranks == 0:
        print(
            "Error: cannot find MPI information in environment variables. I currently search for:"
        )
        for env_name, env_var in env_vars.items():
            print(f"Library: {env_name} , variables {env_var}")
        exit(1)
        return

    mpi_version = sub.run(["mpirun", "--version"], capture_output=True).stdout.decode(
        "utf8"
    )
    if "intel" in mpi_version.lower():
        gdbservers = ""
        if rank == 0:
            print(
                "Error: Intel MPI detected. Please use this command to launch the mdb instead."
            )
            gdbservers = " ".join(
                [f"gdbserver :{port+rank}:{rank};" for rank in range(num_ranks)]
            )
            cmd = [f"\n\tmpirun -n {num_ranks} -gtool"] + [f'"{gdbservers}"'] + args
            print(" ".join(cmd))
        exit(1)
        return

    launch_server(rank=rank, start_port=port, args=args)


def launch_server(rank: int, start_port: int, args: list[str]) -> None:
    """launch a gdb server on the current rank.

    Args:
        rank: rank on which gdb server is running.
        start_port: starting port. Port number will be port+rank. Defaults to 2000.
        args: binary to debug and optional list of arguments for that binary.

    Returns:
        None.
    """
    port = start_port + rank
    sub.run(["gdbserver", f"localhost:{port}"] + args)
    print(f"server on rank {rank} closed")
    return
