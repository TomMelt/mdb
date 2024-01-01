from __future__ import annotations

from multiprocessing.dummy import Pool
from typing import TYPE_CHECKING

import pexpect  # type: ignore

from .mdb_shell import GDBPROMPT
from .utils import parse_ranks

if TYPE_CHECKING:
    from multiprocessing.pool import ThreadPool

    from .mdb_attach import Prog_opts


class Client:
    def __init__(self, prog_opts: Prog_opts) -> None:
        self.ranks: int = prog_opts["ranks"]
        self.host: str = prog_opts["host"]
        self.start_port: int = prog_opts["port"]
        self.breakpt: str = prog_opts["breakpt"]
        self.select: set[int] = parse_ranks(prog_opts["select"])
        self.pool: ThreadPool = Pool(self.ranks)
        self.dbg_procs: list[pexpect.spawn] = []
        return

    def close_procs(self) -> None:
        """Close all open processes."""

        for proc in self.dbg_procs:
            print(f"closing process {proc.pid}")
            proc.close()
        return

    def clear_stdout(self) -> None:
        """Clear stdout from pexpect."""

        def send_command(rank: int) -> None:
            c = self.dbg_procs[rank]
            while True:
                try:
                    c.expect(GDBPROMPT, timeout=0.1)
                    # print(c.before.decode("utf-8"), end="")
                except pexpect.exceptions.TIMEOUT:
                    break
            return

        self.pool.map(send_command, list(range(self.ranks)))

    def connect(self) -> None:
        """Connect to gdb server on each rank."""
        procs = self.pool.map(self.connect_proc, list(range(self.ranks)))
        for p in procs:
            self.dbg_procs.append(p)
        return

    def connect_proc(self, rank: int) -> pexpect.spawn:
        """Connect to a specific gdb server for the given rank.

        Args:
            rank: rank on which gdb server is running.

        Returns:
            a `pexpect.spawn` process which can be used to send commands to the
            gdb server.
        """
        port: int = self.start_port + rank
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
