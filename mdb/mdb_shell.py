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
from subprocess import run
from typing import TYPE_CHECKING, Any, Callable

import matplotlib.pyplot as plt
import numpy as np
import pexpect  # type: ignore

from .utils import (
    parse_ranks,
    print_tabular_output,
    strip_bracketted_paste,
    strip_control_characters,
)

if TYPE_CHECKING:
    from pexpect import spawn

    from .mdb_attach import Prog_opts
    from .mdb_client import Client

INTERACT_ESCAPE = chr(29)  # ctrl+]
INTERACT_CANCEL = chr(3)  # ctrl+c
INTERACT_EOF = chr(4)  # ctrl+d
GDBPROMPT = r"\(gdb\)"
plt.style.use("dark_background")


def buffered_input_filter(
    handle_input: Callable[[str], str]
) -> Callable[[bytes], bytes]:
    """Wrap functions to generate arguments for ``pexpect.interact`` filters.

    Wraps a callback function with a buffer so that instead of receiving each
    character as it is typed, the filter function is given the current command
    string. The wrapper also augments/overrides the interaction with common
    substitutions for control characters:

        - ``Ctrl-d`` will send ``INTERACT_ESCAPE_CHARACTER`` to end the
          interaction instead of ``quit`` to the gdb shell.

    The ``handle_input`` argument is only called after each newline or carriage
    return, and should return characters to be sent to the gdb shell else an
    empty string.

    Note that if ``handle_input`` is to modify the string in any way other than
    by sending new characters to the shell, it must also include the backspace
    characters needed to remove (parts of) the current string and include the
    newline character to execute the command in gdb.

    Args:
        handle_input: function that takes a ``str`` and returns a ``str``.

    Returns:
        function that takes ``bytes`` and returns ``bytes``.
    """

    # closure memory
    buffer: list[str] = []

    def input_filter(s: bytes) -> bytes:
        c = s.decode()
        if c == "\n" or c == "\r":
            response = handle_input("".join(buffer))
            # clear the buffer for next command
            buffer.clear()
            if response:
                return response.encode()
        elif c == INTERACT_EOF:  # catch ctrl-d
            return INTERACT_ESCAPE.encode()
        else:
            buffer.append(c)

        return s

    return input_filter


class mdbShell(cmd.Cmd):
    intro: str = 'mdb - mpi debugger - built on gdb. Type ? for more info. To exit interactive mode type "q", "quit", "Ctrl+D" or "Ctrl+]".'
    hist_file: str = os.path.expanduser("~/.mdb_history")
    hist_filesize: int = 10000
    broadcast_mode: bool = False

    def __init__(self, prog_opts: Prog_opts, client: Client) -> None:
        self.ranks = prog_opts["ranks"]
        self.select_str: str = prog_opts["select"]
        self.select = parse_ranks(prog_opts["select"])
        self.prompt = f"(mdb {self.select_str}) "
        self.client = client
        self.exec_script = prog_opts["exec_script"]
        self.plot_lib = prog_opts["plot_lib"]
        if self.plot_lib == "termgraph":
            try:
                run(["termgraph", "--help"], capture_output=True)
            except FileNotFoundError:
                print("warning: termgraph not found. Defaulting to matplotlib.")
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
        try:
            rank: int = int(line)
        except ValueError:
            print(
                f"warning: unrecognized rank {line}. Must specify an integer for the rank."
            )
            return

        if rank not in self.select:
            print(
                f"warning: rank {rank} is not one of the selected ranks {self.select_str}."
            )
            return

        def input_filter(inp: str) -> str:
            if inp == "exit" or inp == "q" or inp == "quit":
                return INTERACT_ESCAPE
            return ""

        c = self.client.dbg_procs[rank]
        sys.stdout.write("\r(gdb) ")
        c.interact(
            escape_character=INTERACT_ESCAPE,
            input_filter=buffered_input_filter(input_filter),
        )

        # clear whatever might still be in the input buffer
        c.send(INTERACT_CANCEL)

        # write newline incase there was a command in progress when interaction quit
        # to avoid overflowing the (mdb) prompt with the end of the command
        sys.stdout.write("\n")
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
            f"name: {var}\nmin : {results.min()}\nmax : {results.max()}\nmean: {results.mean()}\nn   : {len(results)}"
        )

        if self.plot_lib == "termgraph":
            plt_data_str = "\n".join(
                [", ".join([str(x), str(y)]) for x, y in zip(ranks, results)]
            )
            run(
                split("termgraph --color green"),
                input=plt_data_str,
                encoding="utf-8",
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

        if re.match(r"^[0-9,-]+$", commands[0]):
            select = parse_ranks(commands[0])
            command = " ".join(commands[1:])

        try:
            self.client.pool.starmap(
                send_command, zip(itertools.repeat(command), select)
            )
        except pexpect.EOF:
            self.client.close_procs()

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

        if self.client.dbg_procs is []:
            print("warning: no debug processes running. Please relaunch the debugger")
            return "NULL"

        else:
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
        """Override Cmd.postloop() to save mdb history and close gdb processes."""

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
