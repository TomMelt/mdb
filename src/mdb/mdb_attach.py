# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import asyncio
import functools
import logging
import signal
import socket
import sys

import click
from typing_extensions import TypedDict

from .mdb_client import Client, ClientOpts
from .mdb_shell import mdbShell

ShellOpts = TypedDict(
    "ShellOpts",
    {
        "backend_name": str,
        "exec_script": str | None,
        "plot_lib": str,
        "ranks": int,
        "exchange_select": str,
    },
)


@click.command()
@click.option(
    "-h",
    "--hostname",
    default="",
    show_default=True,
    help="Hostname where exchange server is running.",
)
@click.option(
    "-p",
    "--port",
    default=2000,
    show_default=True,
    help="Starting port address. Each rank's port is assigned as [port_address + rank].",
)
@click.option(
    "-x",
    "--exec-script",
    type=click.File("r"),
    help="Execute a set of mdb commands contained in a script file. This script will run and then normal shell mode will be resumed unless `--interactive=false` is also passed.",
)
@click.option(
    "--interactive",
    default=True,
    help="Controls whether mdb will spawn an interactive debugging shell or not. Intended use is for with `-x/--exec-script`.",
)
@click.option(
    "--log-level",
    default="WARN",
    show_default=True,
    help="Choose minimum level of debug messages: [DEBUG, INFO, WARN, ERROR, CRITICAL]",
)
@click.option(
    "--log-file",
    default="mdb-attach.log",
    show_default=True,
    help="The path to a file to write the logs to. Will create the file if it does not exist. Special values are `stderr` and `stdout`, which correspond to the programs standard error and output respectively.",
)
@click.option(
    "--plot-lib",
    default="termgraph",
    show_default=True,
    help="Plotting library to use. Recommended default is [termgraph] but if this is not available [matplotlib] will be used. [matplotlib] is best if there are many ranks to debug e.g., -n 100.",
)
@click.option(
    "--connection-attempts",
    default=3,
    show_default=True,
    help="Maximum number of failed connection attempts. A connection attempt is made once per second.",
)
def attach(
    hostname: str,
    port: int,
    exec_script: click.File,
    interactive: bool,
    log_level: str,
    log_file: str,
    plot_lib: str,
    connection_attempts: int,
) -> None:
    """Attach to mdb debug server.

    Example:

    $ mdb attach -x script.mdb
    """

    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: %s" % log_level)

    # logic to workout where we are logging to
    logger_kwargs = dict(encoding="utf-8", level=numeric_level)

    if log_file == "stderr":
        logger_kwargs["stream"] = sys.stderr
    elif log_file == "stdout":
        logger_kwargs["stream"] = sys.stdout
    else:
        logger_kwargs["filename"] = log_file

    # init a global logging configuration
    logging.basicConfig(**logger_kwargs)  # type: ignore

    supported_plot_libs = ["termgraph", "matplotlib"]
    if plot_lib not in supported_plot_libs:
        msg = f"warning: unrecognized plot library [{plot_lib}]. Supported libraries are [{supported_plot_libs}]."
        raise ValueError(msg)

    if hostname == "":
        hostname = socket.gethostbyname(socket.gethostname())

    client_opts = {
        "exchange_hostname": hostname,
        "exchange_port": port,
        "connection_attempts": connection_attempts,
    }

    if exec_script is None:
        script = None
    else:
        script = exec_script.name

    shell = attach_shell(
        client_opts,  # type: ignore
        plot_lib,
        script_path=script,
    )

    if not interactive:
        shell.preloop()
    else:
        shell.cmdloop()

    # get the current event loop
    loop = asyncio.get_event_loop()
    loop.close()


def attach_shell(
    client_opts: ClientOpts,
    plot_lib: str,
    script_path: None | str = None,
) -> mdbShell:
    """
    Attach to mdb debug server. Returns the shell instance. Intended use is for
    within wrappers, scripts, or tests.

    For details about the arguments, see the docstring of `attach`.
    """

    client = Client(opts=client_opts)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(client.connect())

    ranks = client.number_of_ranks

    shell_opts: ShellOpts = {
        "backend_name": client.backend_name,
        "exec_script": script_path,
        "plot_lib": plot_lib,
        "ranks": ranks,
        "exchange_select": client.select_str,
    }

    mshell = mdbShell(shell_opts, client)

    def ask_exit(signame: str) -> None:
        # at mshell level we have to disable CTRL+C. We only want to send a
        # signal if there is a debug task running. Cancellation of running
        # tasks is handled in the `do_command` method of `mdbShell`
        return

    for signame in {"SIGINT", "SIGTERM"}:
        loop.add_signal_handler(
            getattr(signal, signame),
            functools.partial(ask_exit, signame),
        )

    return mshell
