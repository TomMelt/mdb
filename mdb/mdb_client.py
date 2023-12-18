import itertools
import os
import re
import sys
from multiprocessing.dummy import Pool

import pexpect

from .mdb_shell import GDBPROMPT
from .utils import parse_ranks


class Client:
    pool = None
    dbg_procs = []
    ranks = None
    select = ""
    host = "localhost"
    start_port = 2000
    program = ""
    breakpt = ""

    def __init__(self, prog_opts):
        self.ranks = prog_opts["ranks"]
        self.host = prog_opts["host"]
        self.start_port = prog_opts["port"]
        self.program = prog_opts["program"]
        self.breakpt = prog_opts["breakpt"]
        self.select = parse_ranks(prog_opts["select"])
        self.pool = Pool(self.ranks)
        if self.breakpt == "":
            self.set_main_breakpoint(self.program)
        return

    def set_main_breakpoint(self, program):
        matches = re.findall(
            r"\bmain_*", os.popen(f"nm {program}").read(), flags=re.IGNORECASE
        )
        if "MAIN__" in matches:
            self.breakpt = "MAIN__"
        else:
            self.breakpt = "main"
        return

    def close_procs(self, sig, frame):
        print("")  # print blank line
        for proc in self.dbg_procs:
            print(f"closing process {proc.pid}")
            proc.close()

        sys.exit(0)
        return

    def connect(self):
        ports = [self.start_port + rank for rank in range(self.ranks)]
        procs = self.pool.starmap(
            connect_proc,
            zip(
                itertools.repeat(self.host),
                ports,
                list(range(self.ranks)),
                itertools.repeat(self.select),
                itertools.repeat(self.program),
                itertools.repeat(self.breakpt),
            ),
        )
        for p in procs:
            self.dbg_procs.append(p)


def connect_proc(host, port, rank, select, program, breakpt):
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
    c.sendline(f"b {breakpt}")
    c.expect(GDBPROMPT)
    c.sendline("c")
    c.expect(GDBPROMPT)
    if rank not in select:
        # we do not need to monitor these processes
        # let them stay in continue mode
        c.sendline("c")
    return c
