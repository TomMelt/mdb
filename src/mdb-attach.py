#!/usr/bin/env python

import pexpect
import signal
import sys
import click
from utils import parse_ranks


dbg_procs = []

@click.command()
@click.option('-n', '--ranks', default='1', help='Rank(s) to debug e.g., 4 will debug ranks 0 to 3, or provide specific ranks 0,2,4-6. Note ranks starts with zero index.')
@click.option('-h', '--host', default='localhost', help='Host machine name. Defaults to localhost.')
@click.option('-p', '--port', default=2000, help='Starting port address. Each rank\'s port is assigned as [port_address + rank].')
@click.option('--program', help='program for gdb to debug.', required=True)
def main(ranks, host, port, program):

    ranks = parse_ranks(ranks)

    prog_opts = dict(ranks=ranks, host=host, port=port, program=program)

    connect(prog_opts)

def connect_proc(host, port, program):
    c = pexpect.spawn(f'gdb -q -ex \"target remote {host}:{port}\" {program}', timeout=None)
    c.sendline('b MAIN__')
    c.sendline('c')
    return c

def close_procs(sig, frame):

    print('')
    for proc in dbg_procs:
        print(f'closing process {proc.pid}')
        proc.close()

    sys.exit(0)

def connect(prog_opts):

    dbg_threads = []

    ranks = prog_opts['ranks']
    port = prog_opts['port']
    host = prog_opts['host']
    program = prog_opts['program']

    for rank in ranks:
        port = port+rank
        c = connect_proc(host, port, program)
        dbg_procs.append(c)

    signal.signal(signal.SIGINT, close_procs)

    while True:
        sys.stdout.write("\r")
        rank = int(input('rank to debug: '))
        c = dbg_procs[rank]
        c.interact()

if __name__ == "__main__":
    main()
