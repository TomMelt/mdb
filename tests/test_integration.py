# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import os
import re
import shlex
from subprocess import Popen, run
from time import sleep
from typing import Union

from mdb.utils import strip_bracketted_paste, strip_control_characters


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


def test_mdb_gdb() -> None:

    # kill any stray mdb sessions
    run(
        shlex.split("pkill -9 mdb"),
        capture_output=True,
    )

    # run the mdb launcher in the background
    Popen(
        shlex.split("mdb launch -b gdb -t examples/simple-mpi.exe -n 2"),
        stdin=None,
        stdout=None,
        stderr=None,
    )

    sleep(1)

    # create a simple mdb script for the test
    with open("integration.mdb", mode="w") as script:
        script.write(script_gdb)

    # run mdb attach and collect the stdout
    result = run(
        shlex.split("mdb attach -x integration.mdb"),
        capture_output=True,
    )

    os.remove("integration.mdb")

    # filter out the escape sequences
    result_txt = result.stdout.decode("utf-8")
    result_txt = strip_control_characters(strip_bracketted_paste(result_txt))
    result_txt = re.sub("\r", "", result_txt)
    result_txt = re.sub("\t", "", result_txt)

    # uncomment this block to write test output
    with open("answer-gdb.stdout", "w") as outfile:
        outfile.write(result_txt)

    with open("tests/output/answer-gdb.stdout", "r") as infile:
        answer_text = "".join(infile.readlines())

    # remove run specific outputs
    result_txt = standardize_output(result_txt)
    answer_text = standardize_output(answer_text)

    assert result_txt == answer_text


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


def test_mdb_lldb() -> None:

    # kill any stray mdb sessions
    run(
        shlex.split("pkill -9 mdb"),
        capture_output=True,
    )

    # run the mdb launcher in the background
    Popen(
        shlex.split("mdb launch -b lldb -t examples/simple-mpi-cpp.exe -n 2"),
        stdin=None,
        stdout=None,
        stderr=None,
    )

    sleep(1)

    # create a simple mdb script for the test
    with open("integration.mdb", mode="w") as script:
        script.write(script_lldb)

    # run mdb attach and collect the stdout
    result = run(
        shlex.split("mdb attach -x integration.mdb"),
        capture_output=True,
    )

    os.remove("integration.mdb")

    # filter out the escape sequences
    result_txt = result.stdout.decode("utf-8")
    result_txt = strip_control_characters(strip_bracketted_paste(result_txt))
    result_txt = re.sub("\r", "", result_txt)
    result_txt = re.sub("\t", "", result_txt)

    # uncomment this block to write test output
    with open("answer-lldb.stdout", "w") as outfile:
        outfile.write(result_txt)

    with open("tests/output/answer-lldb.stdout", "r") as infile:
        answer_text = "".join(infile.readlines())

    # remove run specific outputs
    result_txt = standardize_output(result_txt)
    answer_text = standardize_output(answer_text)

    assert result_txt == answer_text


def test_mdb_timeout() -> None:

    # kill any stray mdb sessions
    run(
        shlex.split("pkill -9 mdb"),
        capture_output=True,
    )
    sleep(1)

    # remove existing log file
    os.remove("mdb-attach.log")
    # run mdb attach without start mdb launch
    run(shlex.split("mdb attach --log-level DEBUG"))

    with open("mdb-attach.log") as logfile:
        result_txt = "".join(logfile.readlines())

    with open("tests/output/timeout.log") as logfile:
        answer_text = "".join(logfile.readlines())

    assert result_txt == answer_text
