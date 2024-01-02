# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

from __future__ import annotations

import cmd
import itertools
import os
import re
import readline
import signal
import sys
from multiprocessing.dummy import Pool
from shlex import split
from subprocess import PIPE, run
from typing import TYPE_CHECKING, Any

import matplotlib.pyplot as plt
import numpy as np

from .utils import (
    parse_ranks,
    print_tabular_output,
    strip_bracketted_paste,
    strip_control_characters,
)

if TYPE_CHECKING:
    from pexpect import spawn  # type: ignore

    from .mdb_attach import Prog_opts
    from .mdb_client import Client

GDBPROMPT = r"\(gdb\)"
plt.style.use("dark_background")


class mdbShell(cmd.Cmd):
    intro: str = 'mdb - mpi debugger - built on gdb. Type ? for more info. To exit interactive mode type "Ctrl+]".'
    hist_file: str = os.path.expanduser("~/.mdb_history")
    hist_filesize: int = 10000

    def __init__(self, prog_opts: Prog_opts, client: Client) -> None:
        self.ranks = prog_opts["ranks"]
        select_str: str = prog_opts["select"]
        self.select = parse_ranks(prog_opts["select"])
        self.prompt = f"(mdb {select_str}) "
        self.client = client
        self.exec_script = prog_opts["exec_script"]
        self.plot_lib = prog_opts["plot_lib"]
        if self.plot_lib == "uplot":
            try:
                run(["uplot", "--help"], capture_output=True)
            except FileNotFoundError:
                print("warning: uplot not found. Defaulting to matplotlib.")
                self.plot_lib = "matplotlib"
        super().__init__()

    def do_interact(self, line: str) -> None:
        """
        Description:
        Jump into interactive mode for a specific rank.

        Example:
        The following command will debug the 2nd process (proc id 1)

            (mdb) interact 1
        """
        rank: int = int(line)
        if rank not in self.select:
            print(f"rank {rank} is not one of the selected ranks {self.select}")
            return
        c = self.client.dbg_procs[rank]
        sys.stdout.write("\r(gdb) ")
        c.interact()
        sys.stdout.write("\r")
        return

    def do_info(self, line: str) -> None:
        """
        Description:
        Print basic statistics (min, mean, max) and produce a bar chart for a
        given variable [var] on all selected processes. This is intended for
        float/integer variables.

        Example:
        The following command will print variable [var] on all selected processes.

            (mdb) pprint [var]
        """

        def send_print(var: str, rank: int) -> tuple[int, float]:
            c = self.client.dbg_procs[rank]
            c.sendline(f"print {var}")
            c.expect(GDBPROMPT)
            output = c.before.decode("utf-8")
            result = 0.0
            for line in output.split("\n"):
                float_regex = r"\d+ = ([+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)"
                match = re.search(float_regex, line)
                if match:
                    try:
                        result = float(match.group(1))
                    except ValueError:
                        print(f"cannot convert variable [{var}] to a float.")
            return rank, result

        var = line
        results: tuple[float] | np.ndarray[float, Any]
        ranks, results = zip(
            *self.client.pool.starmap(
                send_print, zip(itertools.repeat(var), self.select)
            )
        )
        results = np.array(results)

        print(
            f"min : {results.min()}\nmax : {results.max()}\nmean: {results.mean()}\nn   : {len(results)}"
        )

        if self.plot_lib == "uplot":
            plt_data_str = "\n".join(
                [", ".join([str(x), str(y)]) for x, y in zip(ranks, results)]
            )
            run(
                ["uplot", "bar", "-d,", "--xlabel", f"{var}", "--ylabel", "rank"],
                stdout=PIPE,
                input=plt_data_str,
                encoding="ascii",
            )
        else:
            fig, ax = plt.subplots()
            ax.bar(ranks, results)
            ax.set_xlabel("rank")
            ax.set_ylabel("value")
            ax.set_title(var)
            plt.show()

        return

    def do_command(self, line: str) -> None:
        """
        Description:
        Run [command] on every selected process. Alternatively, manually
        specify which ranks to run the command on.

        Example:
        The following command will run gdb command [command] on every process.

            (mdb) command [command]

        The following command will run gdb command [command] on processes 0,3,4 and 5.

            (mdb) command 0,3-5 [command]
        """

        def send_command(command: str, rank: int) -> None:
            c = self.client.dbg_procs[rank]
            c.sendline(command)
            c.expect(GDBPROMPT)
            output = c.before.decode("utf-8")
            output = strip_bracketted_paste(output)
            # prepend rank number to each line of output (excluding first and last)
            lines = [
                f"{rank}:\t" + line + "\r\n" for line in output.split("\r\n")[1:-1]
            ]
            output = "".join(lines)
            print(output)
            return

        command = line
        select = self.select
        commands = command.split(" ")

        if re.match(r"[0-9,-]+", commands[0]):
            select = parse_ranks(commands[0])
            command = " ".join(commands[1:])

        self.client.pool.starmap(send_command, zip(itertools.repeat(command), select))

        return

    def do_quit(self, line: str) -> bool:
        """
        Description:
        Quit mdb.

        Example:
        Quit the mdb debugger using the following command:

            (mdb) quit
        """

        print("\nexiting mdb...")
        self.client.close_procs()
        return True

    def do_shell(self, line: str) -> None:
        """
        Description:
        Run shell (UNIX) command.

        Alias [!]

        Example:
        Run a UNIX shell command from mdb.

            (mdb) !ls
        """
        run(split(line))
        return

    def do_update_winsize(self, line: str) -> None:
        """
        Description:
        Update the each processes terminal window size to match the current
        terminal window size mdb is running in. This is handy if you resize
        your terminal and use [interact] with gdb's tui mode.

        Example:
        Update winsize after resizing your terminal window

            (mdb) update_winsize
        """

        def update_winsize(rank: int) -> None:
            cols, rows = os.get_terminal_size()
            c = self.client.dbg_procs[rank]
            c.setwinsize(rows=rows, cols=cols)
            return

        self.client.pool.map(update_winsize, self.select)
        return

    def do_select(self, line: str) -> None:
        """
        Description:
        Change which rank(s) are manually controlled.

        Example:
        Manually control ranks 0,2,3 and 4 using the following command:

            (mdb) select 0,2-4
        """
        ranks = line
        self.hook_SIGINT()
        self.prompt = f"(mdb {ranks}) "
        self.select = parse_ranks(ranks)
        return

    def do_execute(self, line: str) -> None:
        """
        Description:
        Execute commands from an mdb script file.

        Example:
        Run commands from script file test.mdb

            (mdb) execute test.mdb
        """

        def strip_comments(text: str) -> str | None:
            if re.match(r"^\s*#.*", text):
                return None
            return text

        file = line
        try:
            with open(file) as infile:
                commands = infile.read().splitlines()
                # strip comments from list of commands (lines starting with `#`)
                commands = list(filter(strip_comments, commands))
                self.cmdqueue.extend(commands)
        except FileNotFoundError:
            print(
                f"File [{file}] not found. Please check the file exists and try again."
            )

    def do_status(self, line: str) -> None:
        """
        Description:
        Display status of each processes. Status will be red if at a breakpoint
        and green if not.

        Example:
        Display status of all processes.

            (mdb) status
        """

        def status(rank: int) -> bool:
            c = self.client.dbg_procs[rank]

            # regex to find program counter in gdb backtrace output
            hex_regex = r"#0\s+0[xX][0-9a-fA-F]+"
            c.sendline("backtrace 1")
            c.expect(GDBPROMPT)
            output = c.before.decode("utf-8")
            output = strip_bracketted_paste(output)
            output = strip_control_characters(output)
            match = re.search(hex_regex, output)
            # if program counter hex is not found then the process is at a breakpoint
            if match:
                return False
            else:
                return True

        at_breakpoint: list[bool] = self.client.pool.map(
            status, list(range(self.ranks))
        )

        def status_to_color(rank: int, at_breakpoint: bool) -> str:
            if at_breakpoint:
                return f"\x1b[31m{rank}\x1b[m"
            else:
                return f"\x1b[32m{rank}\x1b[m"

        current_status = list(
            map(status_to_color, list(range(self.ranks)), at_breakpoint)
        )

        print_tabular_output(current_status, cols=32)

        return

    def preloop(self) -> None:
        """Override cmd preloop method to load mdb history."""

        readline.parse_and_bind('"\\e[A": history-search-backward')
        readline.parse_and_bind('"\\e[B": history-search-forward')
        if os.path.exists(self.hist_file):
            readline.read_history_file(self.hist_file)
        if self.exec_script is not None:
            self.onecmd(f"execute {self.exec_script}")
        return

    def postloop(self) -> None:
        """Override cmd postloop method to save mdb history and close gdb processes."""

        readline.set_history_length(self.hist_filesize)
        readline.write_history_file(self.hist_file)
        return

    def hook_SIGINT(self, *args: Any) -> None:
        """Run this function when a signal is caught."""

        pool = Pool(self.ranks)

        def send_sigint(proc: spawn) -> None:
            os.kill(proc.pid, signal.SIGINT)
            return

        pool.map(send_sigint, self.client.dbg_procs)

        def send_interrupt(rank: int) -> None:
            c = self.client.dbg_procs[rank]
            c.sendline("interrupt")
            return

        pool.map(send_interrupt, self.select)

        pool.close()

        # clear the interrupt message from each pexpect stdout stream.
        self.client.clear_stdout()
        return

    def default(self, line: str) -> bool:  # type: ignore[override]
        """Method called on an input line when the command prefix is not recognized."""
        if line == "EOF":
            self.onecmd("quit")
            return True
        else:
            print(
                f"unrecognized command [{line}]. Type help to find out list of possible commands."
            )
            return False
