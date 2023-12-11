import subprocess as sub
import pexpect
import threading
import os
import signal
import sys
import pty

no_ranks = int(os.environ['OMPI_COMM_WORLD_SIZE'])
my_rank = int(os.environ['OMPI_COMM_WORLD_RANK'])

def main():

    launch()

def launch():

    print(f"no of ranks = {no_ranks} , my rank = {my_rank}.")
    port = 2000 + int(my_rank)

    sub.call(['gdbserver', f'localhost:{port}', './a.out'], stdout=sub.DEVNULL)
    print('server closed')

    return

if __name__ == "__main__":
    main()
