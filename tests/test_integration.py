# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import os
import re
import shlex
from subprocess import run
from time import sleep
from typing import Generator, Union

import pytest

# test utilities
from utils import BackgroundProcess

from mdb.utils import strip_bracketted_paste, strip_control_characters

import mdb.mdb_attach


@pytest.fixture(autouse=True)
def slow_down_tests() -> Generator[None, None, None]:
    yield
    sleep(1)
    run(
        shlex.split("pkill -9 mdb"),
        capture_output=True,
    )


def strip_runtime_specific_output(text: str) -> str:
    # remove process ids
    text = re.sub(r"[Pp]rocess \d+", "process [proc id]", text)
    # remove LWP
    text = re.sub(r"(LWP \d+)", "(LWP XXX)", text)
    # remove thread ids
    text = re.sub(r"Thread 0[xX][0-9a-fA-F]+", "Thread [thread id]", text)
    # remove absolute cwd
    text = re.sub(
        r"cmdline = '[\/\w]+/simple-mpi.exe'", "cmdline = simple-mpi.exe", text
    )
    # remove absolute cwd
    text = re.sub(r"cwd = '[\/\w]+'", "cwd = [mdb root]", text)
    # remove absolute exe
    text = re.sub(r"exe = '[\/\w]+/simple-mpi.exe'", "exe = simple-mpi.exe", text)
    # remove program address
    text = re.sub(r"at 0[xX][0-9a-fA-F]+", "at [hex address]", text)
    # remove trailing whitespace (causes
    text = re.sub(r"\s+\n", "\n", text)
    return text


def standardize_output(text: str) -> str:
    # remove process and thread ids and other system specific output
    text = strip_runtime_specific_output(text)

    def filter_mask(line: str) -> Union[str, None]:
        if re.search(r"\d+:Reading.*from remote target...", line):
            return None
        return line

    # required for GitHub CI run
    text = "\n".join(list(filter(filter_mask, text.splitlines())))
    return text


def run_test_for_backend(launch_command: str, name: str, backend_script: str) -> None:

    # run the mdb launcher in the background
    with BackgroundProcess(launch_command):
        # create a simple mdb script for the test
        with open("integration.mdb", mode="w") as script:
            script.write(backend_script)

        # run mdb attach and collect the stdout
        result = run(
            shlex.split("mdb attach -h 127.0.0.1 -p 62000 -x integration.mdb"),
            capture_output=True,
        )

        os.remove("integration.mdb")

        # filter out the escape sequences
        result_txt = result.stdout.decode("utf-8")
        result_txt = strip_control_characters(strip_bracketted_paste(result_txt))
        result_txt = re.sub("\r", "", result_txt)
        result_txt = re.sub("\t", "", result_txt)

        # uncomment this block to write test output
        with open(f"answer-{name}.stdout", "w") as outfile:
            outfile.write(result_txt)

        with open(f"tests/output/answer-{name}.stdout", "r") as infile:
            answer_text = "".join(infile.readlines())

        # remove run specific outputs
        result_txt = standardize_output(result_txt)
        answer_text = standardize_output(answer_text)

        # print(result_txt)

        assert result_txt == answer_text


script_gdb = """# this is a simple test script
!echo hello
command info proc
command b simple-mpi.f90:15
command b simple-mpi.f90:17
command continue
command 0 continue
command bt -1
made-up-command
select 1
command continue
execute deliberately-missing-file.mdb
select 0-1
broadcast start
p 5*5
broadcast stop
command continue
command quit
quit
"""


@pytest.mark.skip(reason="Expected output is out of date")
def test_mdb_gdb() -> None:
    launch_command = "mdb launch -b gdb -t examples/simple-mpi.exe -n 2 -h 127.0.0.1 --log-level=DEBUG -p 62000"
    run_test_for_backend(launch_command, "gdb", script_gdb)


script_lldb = """# this is a simple test script
!echo hello
command process status
command break set -f simple-mpi-cpp.cpp -l 30
command break set -f simple-mpi-cpp.cpp -l 32
command continue
command 0 continue
command bt 1
made-up-command
select 1
command continue
execute deliberately-missing-file.mdb
select 0-1
broadcast start
p 5*5
broadcast stop
command continue
command quit
quit
"""


@pytest.mark.skip(reason="Expected output is out of date")
def test_mdb_lldb() -> None:
    launch_command = "mdb launch -b lldb -t examples/simple-mpi-cpp.exe -n 2 -h 127.0.0.1 --log-level=DEBUG -p 62000"
    run_test_for_backend(launch_command, "lldb", script_lldb)


def test_mdb_timeout() -> None:

    # remove existing log file
    try:
        os.remove("mdb-attach.log")
    except FileNotFoundError:
        pass

    # run mdb attach without start mdb launch
    try:
        mdb.mdb_attach.attach(
            ["-h", "127.0.0.1", "--log-level", "DEBUG", "-p", "62000"],
            standalone_mode=False,
        )
    except ConnectionError as e:
        assert str(e) == "couldn't connect to exchange server at 127.0.0.1:62000."


def test_mdb_connect() -> None:
    launch_command = "mdb launch -b gdb -t examples/simple-mpi-cpp.exe -n 2 -h 127.0.0.1 --log-level=DEBUG -p 62000"

    with BackgroundProcess(launch_command):
        loop, shell = mdb.mdb_attach.attach_shell(
            {
                "exchange_hostname": "127.0.0.1",
                "exchange_port": 62000,
                "connection_attempts": 3,
            },
            "termgraph",
        )
        loop.close()
