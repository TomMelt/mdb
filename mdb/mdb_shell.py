# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

from __future__ import annotations

import asyncio
import cmd
import os
import re
import readline
import shlex
from shlex import split
from subprocess import run
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt

from .utils import (
    parse_ranks,
    prepend_ranks,
    print_tabular_output,
    strip_bracketted_paste,
    strip_control_characters,
)

if TYPE_CHECKING:
    from .mdb_attach import ShellOpts
    from .mdb_client import Client


plt.style.use("dark_background")


def sort_debug_response(response):
    output = response["result"]
    output = sorted(output, key=lambda result: result["rank"])
    return output


def pretty_print_response(response):
    lines = []
    for result in response:
        lines.append(prepend_ranks(output=result["result"], rank=result["rank"]))
    combined_output = (72 * "*" + "\n").join(lines)
    print(combined_output)


def extract_float(line):
    float_regex = r"\d+ = ([+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)"
    match = re.search(float_regex, line)
    if match:
        try:
            result = float(match.group(1))
        except ValueError:
            print(f"cannot convert variable [{var}] to a float.")

    return result


def info(response, var):
    results = list(map(lambda x: x["result"]))
    ranks = list(map(lambda x: x["rank"]))

    print(
        f"name: {var}\nmin : {results.min()}\nmax : {results.max()}\nmean: {results.mean()}\nn   : {len(results)}"
    )

    # if self.plot_lib == "termgraph":
    plt_data_str = "\n".join(
        [", ".join([str(x), str(y)]) for x, y in zip(ranks, results)]
    )
    run(
        shlex.split("termgraph --color green"),
        input=plt_data_str,
        encoding="utf-8",
    )
    # else:
    #     fig, ax = plt.subplots()
    #     ax.bar(ranks, results)
    #     ax.set_xlabel("rank")
    #     ax.set_ylabel("value")
    #     ax.set_title(var)
    #     plt.show()


class mdbShell(cmd.Cmd):
    intro: str = 'mdb - mpi debugger - built on various backends. Type ? for more info. To exit interactive mode type "q", "quit", "Ctrl+D" or "Ctrl+]".'
    hist_file: str = os.path.expanduser("~/.mdb_history")
    hist_filesize: int = 10000
    broadcast_mode: bool = False

    def __init__(self, shell_opts: ShellOpts, client: Client) -> None:
        self.ranks = shell_opts["ranks"]
        self.select_str: str = shell_opts["select"]
        self.select = parse_ranks(shell_opts["select"])
        self.backend = shell_opts["backend"]
        self.prompt = f"(mdb {self.select_str}) "
        self.client = client
        self.exec_script = shell_opts["exec_script"]
        self.plot_lib = shell_opts["plot_lib"]
        if self.plot_lib == "termgraph":
            try:
                run(["termgraph", "--help"], capture_output=True)
            except FileNotFoundError:
                print("warning: termgraph not found. Defaulting to matplotlib.")
                self.plot_lib = "matplotlib"
        super().__init__()

    def do_stats(self, line: str) -> None:
        """
        Description:
        Print basic statistics (min, mean, max) and produce a bar chart for a
        given variable [var] on all selected processes. This is intended for
        float/integer variables.

        Example:
        The following command will plot a graph of variable [var] on all selected processes.

            (mdb) stats [var]
        """

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.client.run_command(f"print {line}"))
        response = sort_debug_response(response)
        info(response=response, var=line)

    def do_command(self, line: str) -> None:
        """
        Description:
        Run [command] on every selected process. Alternatively, manually
        specify which ranks to run the command on.

        Example:
        The following command will run {self.backend} command [command] on every process.

            (mdb) command [command]

        The following command will run {self.backend} command [command] on processes 0,3,4 and 5.

            (mdb) command 0,3-5 [command]
        """

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.client.run_command(line))
        response = sort_debug_response(response)
        pretty_print_response(response)

        return

    def do_quit(self, line: str) -> bool:
        """
        Description:
        Quit mdb.

        Example:
        Quit the mdb debugger using the following command:

            (mdb) quit
        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.client.run_command("shutdown"))
        loop.run_until_complete(self.client.close())
        print("\nexiting mdb...")
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
        self.select_str = line
        self.hook_SIGINT()
        self.prompt = f"(mdb {self.select_str}) "
        self.select = parse_ranks(self.select_str)
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
            c.expect(self.prompt)
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

    def do_broadcast(self, line: str) -> None:
        """
        Description:
        Broadcast mode (bcm) sends commands to the selected ranks (see help
        select for more info). Broadcast mode is enabled/(disabled) by typing
        broadcast start/(stop). To exit broadcast mode, enter command
        [broadcast stop] or [quit] or press CTRL+D.

        Example:
        The following command will start broadcast mode.

            (mdb) broadcast start
        """

        if line.lower() == "start":
            self.broadcast_mode = True
        elif line.lower() == "stop":
            self.broadcast_mode = False
        else:
            print(
                f"warning: unrecognized option {line}. Valid options are [start] or [stop]."
            )

        if self.broadcast_mode:
            self.prompt = f"\r\x1b[33m(bcm {self.select_str})\x1b[m "
        else:
            self.prompt = f"\r(mdb {self.select_str}) "

        return

    def precmd(self, line: str) -> str:
        """Override Cmd.precmd() to only run the command if debug processes are open."""

        if line in ["quit", "EOF"]:
            if self.broadcast_mode:
                return "broadcast stop"
            return line

        if line == "broadcast stop":
            return line

        if self.broadcast_mode:
            line = "command " + line
            return line

        return line

    def preloop(self) -> None:
        """Override Cmd.preloop() to load mdb history."""

        readline.parse_and_bind('"\\e[A": history-search-backward')
        readline.parse_and_bind('"\\e[B": history-search-forward')
        if os.path.exists(self.hist_file):
            readline.read_history_file(self.hist_file)
        if self.exec_script is not None:
            self.onecmd(f"execute {self.exec_script}")
        return

    def postloop(self) -> None:
        """Override Cmd.postloop() to save mdb history."""

        readline.set_history_length(self.hist_filesize)
        readline.write_history_file(self.hist_file)
        return

    def default(self, line: str) -> bool:  # type: ignore[override]
        """Method called on an input line when the command prefix is not recognized."""
        if line == "EOF":
            # Cmd converts CTRL+D to "EOF"
            self.onecmd("quit")
            return True
        elif line == "NULL":
            # do nothing
            # useful to have a fake command for precmd()
            return False
        else:
            print(
                f"unrecognized command [{line}]. Type help to find out list of possible commands."
            )
            return False
