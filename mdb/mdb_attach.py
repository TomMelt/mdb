import pexpect
import signal
import sys
import click
from .utils import parse_ranks
import cmd
from multiprocessing.dummy import Pool
import itertools
import re
import numpy as np
import matplotlib.pyplot as plt

dbg_procs = []
plt.style.use("dark_background")
GDBPROMPT = r"\(gdb\)"

pool = Pool(8)


@click.command()
@click.option(
    "-n",
    "--ranks",
    default=1,
    show_default=True,
    help="Total number of ranks to debug.",
)
@click.option(
    "-s",
    "--select",
    default="",
    show_default=True,
    help="Rank(s) to debug e.g., 0,3-5 will debug ranks 0,3,4 and 5. If empty all ranks will be selected. Note ranks starts with zero index.",
)
@click.option(
    "-h",
    "--host",
    default="localhost",
    show_default=True,
    help="Host machine name.",
)
@click.option(
    "-p",
    "--port",
    default=2000,
    show_default=True,
    help="Starting port address. Each rank's port is assigned as [port_address + rank].",
)
@click.option("--program", help="program for gdb to debug.", required=True)
def attach(ranks, select, host, port, program):
    if select == "":
        select = ",".join(list(range(ranks)))

    prog_opts = dict(ranks=ranks, select=select, host=host, port=port, program=program)

    connect(prog_opts)


def close_procs(sig, frame):
    print("")
    for proc in dbg_procs:
        print(f"closing process {proc.pid}")
        proc.close()

    sys.exit(0)


def connect_proc(host, port, rank, select, program):
    print(f"connecting to port: {port}")
    c = pexpect.spawn(f"gdb -q {program}", timeout=None)
    c.expect(GDBPROMPT)
    print(c.before.decode("utf-8"), end="")
    c.sendline("set pagination off")
    c.expect(GDBPROMPT)
    c.sendline("set confirm off")
    c.expect(GDBPROMPT)
    c.sendline(f"target remote {host}:{port}")
    c.expect(GDBPROMPT)
    c.sendline("b MAIN__")
    c.expect(GDBPROMPT)
    c.sendline("c")
    c.expect(GDBPROMPT)
    if rank not in select:
        # we do not need to monitor these processes
        # let them stay in continue mode
        c.sendline("c")
    return c


def connect(prog_opts):
    ranks = prog_opts["ranks"]
    start_port = prog_opts["port"]
    host = prog_opts["host"]
    program = prog_opts["program"]
    select = parse_ranks(prog_opts["select"])

    ports = [start_port + rank for rank in range(ranks)]
    procs = pool.starmap(
        connect_proc,
        zip(
            itertools.repeat(host),
            ports,
            list(range(ranks)),
            itertools.repeat(select),
            itertools.repeat(program),
        ),
    )
    for p in procs:
        dbg_procs.append(p)

    signal.signal(signal.SIGINT, close_procs)
    mshell = mdbShell(prog_opts)
    mshell.cmdloop()


class mdbShell(cmd.Cmd):
    intro = "mdb - mpi debugger - built on gdb. Type ? for more info"
    prompt = "(mdb) "
    select = list()
    ranks = list()

    def __init__(self, prog_opts):
        self.ranks = prog_opts["ranks"]
        select_str = prog_opts["select"]
        self.select = parse_ranks(select_str)
        self.prompt = f"(mdb {select_str}) "
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
        if rank not in self.select:
            print(f"rank {rank} is not one of the selected ranks {self.select}")
            return
        c = dbg_procs[rank]
        sys.stdout.write("\r(gdb) ")
        c.interact()
        sys.stdout.write("\r")
        return

    def do_print(self, var):
        """
        Description:
        Print [var] on every selected process.

        Example:
        The following command will print variable [var] on all selected processes.

            (mdb) pprint [var]
        """

        def send_print(var, rank):
            c = dbg_procs[rank]
            c.sendline(f"print {var}")
            c.expect(GDBPROMPT)
            output = c.before.decode("utf-8")
            result = 0.0
            for line in output.split("\n"):
                float_regex = r"\d+ = ([+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)"
                m = re.search(float_regex, line)
                if m:
                    result = m.group(1)
                    try:
                        result = float(result)
                    except ValueError:
                        print(f"cannot convert variable [{var}] to a float.")
                        return
            return rank, result

        ranks = []
        results = []
        for rank, result in pool.starmap(
            send_print, zip(itertools.repeat(var), self.select)
        ):
            ranks.append(str(rank))  # string for barchart labels
            results.append(result)

        results = np.array(results)
        print(
            f"min : {results.min()}\nmax : {results.max()}\nmean: {results.mean()}\nn    : {len(results)}"
        )

        fig, ax = plt.subplots()
        ax.bar(ranks, results)
        ax.set_xlabel("rank")
        ax.set_ylabel("value")
        ax.set_title(var)
        plt.show()

        return

    def do_clearbuffers(self, args):
        """
        Description:
        Clear all process stdout buffers.

        Example:
        The following command will clear the stdout buffer for each process.

            (mdb) clearbuffers
        """
        for rank in range(self.ranks):
            c = dbg_procs[rank]
            while True:
                if c.before:
                    c.expect(r".+")
                else:
                    break
        print("cleared")

    def do_command(self, command):
        """
        Description:
        Run [command] on every process.

        Example:
        The following command will run gdb command [command] on every process.

            (mdb) pcommand [command]
        """

        def send_command(command, rank):
            c = dbg_procs[rank]
            c.sendline(command)
            c.expect(GDBPROMPT)
            print(f"{rank}: " + c.before.decode("utf-8"), end="\n")
            return

        pool.starmap(send_command, zip(itertools.repeat(command), self.select))

        return
