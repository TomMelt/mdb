# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

from __future__ import annotations

import asyncio
import cmd
import functools
import os
import re
import readline
import shlex
import signal
from shlex import split
from subprocess import run
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np

from .backend import backends
from .utils import (
    extract_float,
    parse_ranks,
    pretty_print_response,
    sort_debug_response,
)

if TYPE_CHECKING:
    from .mdb_attach import ShellOpts
    from .mdb_client import Client


plt.style.use("dark_background")


class mdbShell(cmd.Cmd):
    intro: str = (
        'mdb - mpi debugger - built on various backends. Type ? for more info. To exit interactive mode type "q", "quit", "Ctrl+D" or "Ctrl+]".'
    )
    hist_file: str = os.path.expanduser("~/.mdb_history")
    hist_filesize: int = 10000
    broadcast_mode: bool = False

    def __init__(self, shell_opts: ShellOpts, client: Client) -> None:
        self.aliases = {
            "bc": self.do_broadcast,
            "q": self.do_quit,
            "EOF": self.do_quit,
            "h": self.do_help,
        }

        self.ranks = shell_opts["ranks"]
        self.exchange_select_str = shell_opts["exchange_select"]
        self.exchange_select = parse_ranks(self.exchange_select_str)
        self.select_str = self.exchange_select_str
        self.select = self.exchange_select
        backend_name = shell_opts["backend_name"].lower()
        if backend_name in backends:
            self.backend = backends[backend_name]()
        else:
            raise ValueError(f"Debugger backend is not supported: {backend_name}")

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

    def do_dump(self, line: str) -> None:
        """
        Description:
        Dump variable in memory to binary file
        Example:
        The following command will dump variable [var] to a file with the name [var].dmp.[rank].

            (mdb) dump [var]
        """

        if not re.search("gdb", self.client.backend_name):
            print("Error: this feature is only supported for gdb-like backends")
            return

        var = line

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self.client.run_command(
                f"dump binary value {var}.dmp.$RANK$ {var}", self.select
            )
        )
        print("written data to disk")

    def do_plot(self, line: str) -> None:
        """
        Description:
        Print basic statistics (min, mean, max) and produce a bar chart for a
        given variable [var] on all selected processes. This is intended for
        float/integer variables.

        Example:
        The following command will plot a graph of variable [var] on all selected processes.

            (mdb) plot [var]
        """

        var = line

        loop = asyncio.get_event_loop()
        command_response = loop.run_until_complete(
            self.client.run_command(f"print {var}", self.select)
        )
        response = sort_debug_response(command_response.data["results"])

        ranks = np.array(list(response.keys()))

        try:
            data = np.array(
                list(
                    map(
                        lambda v: extract_float(v, backend=self.backend),
                        response.values(),
                    )
                )
            )

            print("min  = ", np.min(data))
            print("max  = ", np.max(data))
            print("mean = ", np.mean(data))

            if self.plot_lib == "termgraph":
                plt_data_str = "\n".join(
                    [", ".join([str(x), str(y)]) for x, y in zip(ranks, data)]
                )
                run(
                    shlex.split("termgraph --color green"),
                    input=plt_data_str,
                    encoding="utf-8",
                )
            else:
                fig, ax = plt.subplots()
                ax.bar(ranks, data)
                ax.set_xlabel("rank")
                ax.set_ylabel("value")
                ax.set_title(var)
                plt.show()

        except Exception as e:
            print(f"[do_plot] Exception: {e}")

    def do_command(self, line: str) -> None:
        """
        Description:
        Run [command] on every selected process. Alternatively, manually
        specify which ranks to run the command on.

        Example:
        The following command will run "print myvar" command on every process.

            (mdb) command print myvar

        The following command will run "print myvar" command on processes 0,3,4 and 5.

            (mdb) command 0,3-5 print myvar
        """

        command = line
        select = self.select
        commands = command.split(" ")

        if re.match(r"^[0-9,-]+$", commands[0]):
            select = parse_ranks(commands[0])
            command = " ".join(commands[1:])

        loop = asyncio.get_event_loop()

        def ask_exit(signame: str) -> None:
            # we tell debug process to send a command and not listen for a
            # response, since there is already a task in the event queue that
            # is waiting for a response
            asyncio.create_task(self.client.send_interrupt(signame=signame))

        for signame in {"SIGINT", "SIGTERM"}:
            loop.add_signal_handler(
                getattr(signal, signame),
                functools.partial(ask_exit, signame),
            )

        command_response = loop.run_until_complete(
            self.client.run_command(command, select)
        )

        def ask_remain_calm(signame: str) -> None:
            # we tell debug process to send a command and not listen for a
            # response, since there is already a task in the event queue that
            # is waiting for a response
            print("remain calm")
            return

        for signame in {"SIGINT", "SIGTERM"}:
            loop.remove_signal_handler(
                getattr(signal, signame),
            )
            loop.add_signal_handler(
                getattr(signal, signame),
                functools.partial(ask_remain_calm, signame),
            )

        if command_response.msg_type == "exchange_command_response":
            response = sort_debug_response(command_response.data["results"])
            pretty_print_response(response)
        else:
            print("Received unexpected message type: %s", command_response.msg_type)
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

    def do_select(self, line: str) -> None:
        """
        Description:
        Change which rank(s) are manually controlled.

        Example:
        Manually control ranks 0,2,3 and 4 using the following command:

            (mdb) select 0,2-4
        """
        if line == "":
            self.select_str = f"0-{self.ranks - 1}"
        else:
            self.select_str = line
        self.select = parse_ranks(self.select_str)
        if not set(self.select) <= set(self.exchange_select):
            msg = "Error: user specified option [select] must be subset of available ranks (check mdb launch command)."
            msg += f"\nselect = [{self.select_str}] but available ranks are [{self.exchange_select_str}]."
            print(msg)
            return
        self.prompt = f"(mdb {self.select_str}) "
        return

    def do_execute(self, line: str) -> None:
        """
        Description:
        Execute commands from an mdb script file.

        Example:
        Run commands from script file test.mdb

            (mdb) execute test.mdb
        """
        file = line
        try:
            with open(file) as infile:
                contents = infile.read()
            self.execute_script(contents, queue=True)
        except FileNotFoundError:
            print(
                f"File [{file}] not found. Please check the file exists and try again."
            )

    def execute_script(self, script: str, queue: bool = False) -> None:
        def strip_comments(text: str) -> str | None:
            if re.match(r"^\s*#.*", text):
                return None
            return text

        commands = script.splitlines()
        # strip comments from list of commands (lines starting with `#`)
        commands = list(filter(strip_comments, commands))

        if queue:
            self.cmdqueue.extend(commands)
        else:
            for command in commands:
                self.onecmd(self.precmd(command))

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
            self.prompt = f"(bcm {self.select_str}) "
        else:
            self.prompt = f"(mdb {self.select_str}) "

        return

    def precmd(self, line: str) -> str:
        """Override Cmd.precmd() to only run the command if debug processes are open."""

        if line in ["q", "quit", "EOF"]:
            if self.broadcast_mode:
                if line == "EOF":
                    print()
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

    def default(self, line: str) -> bool | None:  # type: ignore[override]
        """Method called on an input line when the command prefix is not recognized."""
        cmd, arg, line = self.parseline(line)
        if cmd in self.aliases:
            return self.aliases[cmd](str(arg))
        else:
            print(
                f"unrecognized command [{line}]. Type help to find out list of possible commands."
            )
            return False

    def do_help(self, arg: str) -> None:
        """Print help text for commands and aliases."""
        if arg in self.aliases:
            arg = self.aliases[arg].__name__[3:]
        cmd.Cmd.do_help(self, arg)
