#!/usr/bin/env python

import pexpect
import signal
import sys
import click
from utils import parse_ranks
import cmd


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
    # shell_cmd = f'gdb -q -ex \"target remote {host}:{port}\" {program} > /tmp/log.{port}'
    # c = pexpect.spawn('/bin/bash', ['-c', shell_cmd], timeout=None)
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

    ranks = prog_opts['ranks']
    port = prog_opts['port']
    host = prog_opts['host']
    program = prog_opts['program']

    for rank in ranks:
        port = port+rank
        c = connect_proc(host, port, program)
        dbg_procs.append(c)

    signal.signal(signal.SIGINT, close_procs)

    mdbShell().cmdloop()
    # while True:
    #     sys.stdout.write("\r")
    #     command = int(input('(mdb) '))
    #     parse_command(command)

class mdbShell(cmd.Cmd):
    intro = 'mdb - mpi debugger - built on gdb. Type ? for more info'
    prompt = '(mdb) '

    def do_interact(self, rank):
        """
        Description:
        Jump into interactive mode for a specific rank.

        Example:
        The following command will debug the 2nd process (proc id 1)

            (mdb) interact 1
        """
        rank = int(rank)
        c = dbg_procs[rank]
        c.interact()
        sys.stdout.write("\r")
        return

    def do_pcommand(self, command):
        """
        Description:
        Run [command] on every process.

        Example:
        The following command will run [command] on every process.

            (mdb) pcommand
        """
        for c in dbg_procs:
            c.sendline(command)
            c.expect('(gdb)')
            print("c.before = \n", c.before.decode('utf-8'))
            print("c.after = \n", c.after.decode('utf-8'))
        return


if __name__ == "__main__":
    main()
