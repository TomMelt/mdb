#!/usr/bin/env python

import subprocess as sub
import os
import sys
import click
import signal
from utils import parse_ranks


no_ranks = int(os.environ['OMPI_COMM_WORLD_SIZE'])
my_rank = int(os.environ['OMPI_COMM_WORLD_RANK'])
my_proc = None

@click.command()
@click.option('-n', '--ranks', default='1', help='Rank(s) to debug e.g., 4 will debug ranks 0 to 3, or provide specific ranks 0,2,4-6. Note ranks starts with zero index.')
@click.option('-p', '--port', default=2000, help='Starting port address. Each rank\'s port is assigned as [port_address + rank].')
@click.option('--args', help='program and args for gdb')
def main(ranks, port, args):

    ranks = parse_ranks(ranks)
    launch(ranks, port, args)

def launch(ranks, port, args):

    print(f"no of ranks = {no_ranks} , my rank = {my_rank}.")
    port = port + int(my_rank)

    signal.signal(signal.SIGINT, close_procs)

    if my_rank in ranks:
        my_proc = sub.run(['gdbserver', f'localhost:{port}', f'{args}'])

    print(f'server on rank {my_rank} closed')

    return

def close_procs(sig, frame):

    print(f'Terminating process {my_proc}')
    my_proc.terminate()
    sys.exit(0)

if __name__ == "__main__":
    main()
