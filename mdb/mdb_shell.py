import cmd
import itertools
import os
import re
import readline
import sys
from subprocess import PIPE, run

import matplotlib.pyplot as plt
import numpy as np

from .utils import parse_ranks

GDBPROMPT = r"\(gdb\)"
plt.style.use("dark_background")


class mdbShell(cmd.Cmd):
    intro = 'mdb - mpi debugger - built on gdb. Type ? for more info. To exit interactive mode type "Ctrl+]".'
    prompt = "(mdb) "
    hist_file = os.path.expanduser("~/.mdb_history")
    hist_filesize = 10000
    select = list()
    ranks = list()
    client = None
    plot_lib = "uplot"

    def __init__(self, prog_opts, client):
        self.ranks = prog_opts["ranks"]
        select_str = prog_opts["select"]
        self.select = parse_ranks(select_str)
        self.prompt = f"(mdb {select_str}) "
        self.client = client
        self.plot_lib = prog_opts["plot_lib"]
        if self.plot_lib == "uplot":
            try:
                run(["uplot", "--help"], capture_output=True)
            except FileNotFoundError:
                print("warning: uplot not found. Defaulting to matplotlib.")
                self.plot_lib = "matplotlib"
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
        c = self.client.dbg_procs[rank]
        sys.stdout.write("\r(gdb) ")
        c.interact()
        sys.stdout.write("\r")
        return

    def do_info(self, var):
        """
        Description:
        Print basic statistics (min, mean, max) and produce a bar chart for a
        given variable [var] on all selected processes. This is intended for
        float/integer variables.

        Example:
        The following command will print variable [var] on all selected processes.

            (mdb) pprint [var]
        """

        def send_print(var, rank):
            c = self.client.dbg_procs[rank]
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
        for rank, result in self.client.pool.starmap(
            send_print, zip(itertools.repeat(var), self.select)
        ):
            ranks.append(str(rank))  # string for barchart labels
            results.append(result)

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

    def do_command(self, command):
        """
        Description:
        Run [command] on every process.

        Example:
        The following command will run gdb command [command] on every process.

            (mdb) command [command]
        """

        def send_command(command, rank):
            c = self.client.dbg_procs[rank]
            c.sendline(command)
            c.expect(GDBPROMPT)
            print(f"{rank}: " + c.before.decode("utf-8"), end="\n")
            return

        self.client.pool.starmap(
            send_command, zip(itertools.repeat(command), self.select)
        )

        return

    def do_quit(self, command):
        """
        Description:
        Quit mdb.

        Example:
        Quit the mdb debugger using the following command:

            (mdb) quit
        """

        print("\nexiting mdb...")
        return True

    def preloop(self):
        """
        Override cmd preloop method to load mdb history.
        """
        if os.path.exists(self.hist_file):
            readline.read_history_file(self.hist_file)

    def postloop(self):
        """
        Override cmd postloop method to save mdb history and close gdb processes.
        """
        readline.set_history_length(self.hist_filesize)
        readline.write_history_file(self.hist_file)
        self.client.close_procs()

    def hook_SIGINT(self, *args):
        """
        Run this function when a signal is caught.
        """
        print("SIGINT signal caught. Need to implement gdb interrupt.")

    def default(self, line):
        if line == "EOF":
            self.do_quit(None)
            return True
        return
