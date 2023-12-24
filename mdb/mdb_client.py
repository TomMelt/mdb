import itertools
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
    breakpt = "main"

    def __init__(self, prog_opts):
        self.ranks = prog_opts["ranks"]
        self.host = prog_opts["host"]
        self.start_port = prog_opts["port"]
        if prog_opts["breakpt"] != "":
            self.breakpt = prog_opts["breakpt"]
        self.select = parse_ranks(prog_opts["select"])
        self.pool = Pool(self.ranks)
        return

    def close_procs(self):
        for proc in self.dbg_procs:
            print(f"closing process {proc.pid}")
            proc.close()

        sys.exit(0)
        return

    def connect(self):
        procs = self.pool.map(self.connect_proc, list(range(self.ranks)))
        for p in procs:
            self.dbg_procs.append(p)

    def clear_stdout(self):
        """
        Clear stdout from pexpect.
        """

        def send_command(rank):
            c = self.dbg_procs[rank]
            try:
                c.expect(GDBPROMPT, timeout=0.1)
            except pexpect.exceptions.TIMEOUT:
                pass
            return

        self.pool.map(send_command, list(range(self.ranks)))

        return

    def connect_proc(self, rank):
        port = self.start_port + rank
        print(f"connecting to port: {port}")
        c = pexpect.spawn("gdb -q", timeout=None)
        c.expect(GDBPROMPT)
        print(c.before.decode("utf-8"), end="")
        c.sendline("set pagination off")
        c.expect(GDBPROMPT)
        c.sendline("set confirm off")
        c.expect(GDBPROMPT)
        c.sendline(f"target remote {self.host}:{port}")
        c.expect(GDBPROMPT)
        c.sendline(f"b {self.breakpt}")
        c.expect(GDBPROMPT)
        c.sendline("c")
        c.expect(GDBPROMPT)
        if rank not in self.select:
            # we do not need to monitor these processes
            # let them stay in continue mode
            c.sendline("c")
        return c
