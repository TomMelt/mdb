import pexpect
import signal
import sys
import click
from .utils import parse_ranks
import cmd

dbg_procs = []
GDBPROMPT = r'\(gdb\)'

@click.command()
@click.option('-n', '--ranks', default=1, help='Total number of ranks to debug.')
@click.option('-s', '--select', default='all', help='Rank(s) to debug e.g., 4 will debug ranks 0 to 3. Note ranks starts with zero index.')
@click.option('-h', '--host', default='localhost', help='Host machine name. Defaults to localhost.')
@click.option('-p', '--port', default=2000, help='Starting port address. Each rank\'s port is assigned as [port_address + rank].')
@click.option('--program', help='program for gdb to debug.', required=True)
def attach(ranks, select, host, port, program):

    if select == 'all':
        select = list(range(ranks))
    else:
        select = parse_ranks(select)

    prog_opts = dict(ranks=ranks, select=select, host=host, port=port, program=program)

    connect(prog_opts)

def connect_proc(host, port, program):
    c = pexpect.spawn(f'gdb -q {program}', timeout=None)
    # shell_cmd = f'gdb -q -ex \"target remote {host}:{port}\" {program} > /tmp/log.{port}'
    # c = pexpect.spawn('/bin/bash', ['-c', shell_cmd], timeout=None)
    c.expect(GDBPROMPT)
    print(c.before.decode('utf-8'), end='')
    c.sendline(f'target remote {host}:{port}')
    c.expect(GDBPROMPT)
    c.sendline('b MAIN__')
    c.expect(GDBPROMPT)
    c.sendline('c')
    c.expect(GDBPROMPT)
    return c

def close_procs(sig, frame):

    print('')
    for proc in dbg_procs:
        print(f'closing process {proc.pid}')
        proc.close()

    sys.exit(0)

def connect(prog_opts):

    ranks = prog_opts['ranks']
    start_port = prog_opts['port']
    host = prog_opts['host']
    program = prog_opts['program']

    for rank in range(ranks):
        port = start_port+rank
        print("port = \n", port)
        c = connect_proc(host, port, program)
        dbg_procs.append(c)

    signal.signal(signal.SIGINT, close_procs)

    mshell = mdbShell(prog_opts)
    mshell.cmdloop()

class mdbShell(cmd.Cmd):
    intro = 'mdb - mpi debugger - built on gdb. Type ? for more info'
    prompt = '(mdb) '
    select = list()
    ranks = list()

    def __init__(self, prog_opts):
        self.ranks = prog_opts['ranks']
        self.select = prog_opts['select']
        super().__init__()

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
        sys.stdout.write("\r(gdb) ")
        c.interact()
        sys.stdout.write("\r")
        return

    def do_pcommand(self, command):
        """
        Description:
        Run [command] on every process.

        Example:
        The following command will run gdb command [command] on every process.

            (mdb) pcommand [command]
        """
        for rank in range(self.ranks):
            c = dbg_procs[rank]
            if rank in self.select:
                c.sendline(command)
                c.expect(GDBPROMPT)
                print(c.before.decode('utf-8'), end='')
            else:
                c.sendline('c')
        return

    def do_select(self, select):
        """
        Description:
        Select subset of ranks to debug.

        Example:
        The following command will activate ranks [0, 1]. Other ranks will run but in [continue] mode.

            (mdb) select 0,1
        """
        self.select = parse_ranks(select)
        self.prompt = f'(mdb {ranks}) '
        return

if __name__ == "__main__":
    main()
