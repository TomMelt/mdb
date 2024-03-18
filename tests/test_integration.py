# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import os
import re
import shlex
from subprocess import Popen, run
from typing import Union

from mdb.utils import strip_bracketted_paste, strip_control_characters

script_text = """# this is a simple test script
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
status
select 0-1
broadcast start
p 5*5
broadcast stop
command continue
command quit
quit
"""

ans_text = """hello
mdb - mpi debugger - built on various backends. Type ? for more info. To exit interactive mode type "q", "quit", "Ctrl+D" or "Ctrl+]".
0:process 43665
0:cmdline = '/home/melt/sync/cambridge/projects/side/mdb/examples/simple-mpi.exe'
0:cwd = '/home/melt/sync/cambridge/projects/side/mdb'
0:exe = '/home/melt/sync/cambridge/projects/side/mdb/examples/simple-mpi.exe'
************************************************************************
1:process 43664
1:cmdline = '/home/melt/sync/cambridge/projects/side/mdb/examples/simple-mpi.exe'
1:cwd = '/home/melt/sync/cambridge/projects/side/mdb'
1:exe = '/home/melt/sync/cambridge/projects/side/mdb/examples/simple-mpi.exe'

0:Breakpoint 2 at 0x5555555552da: file simple-mpi.f90, line 15.
************************************************************************
1:Breakpoint 2 at 0x5555555552da: file simple-mpi.f90, line 15.

0:Breakpoint 3 at 0x5555555552f6: file simple-mpi.f90, line 17.
************************************************************************
1:Breakpoint 3 at 0x5555555552f6: file simple-mpi.f90, line 17.

0:Continuing.
0:[New Thread 0x7ffff6e0c640 (LWP 43670)]
0:[New Thread 0x7ffff660b640 (LWP 43673)]
0:
0:Thread 1 "simple-mpi.exe" hit Breakpoint 2, simple () at simple-mpi.f90:15
0:15  var = 10.*process_rank
************************************************************************
1:Continuing.
1:[New Thread 0x7ffff6e0c640 (LWP 43671)]
1:[New Thread 0x7ffff660b640 (LWP 43672)]
1:
1:Thread 1 "simple-mpi.exe" hit Breakpoint 2, simple () at simple-mpi.f90:15
1:15  var = 10.*process_rank

0:Continuing.
0:
0:Thread 1 "simple-mpi.exe" hit Breakpoint 3, simple () at simple-mpi.f90:17
0:17  if (process_rank == 0) then
************************************************************************

0:#0  simple () at simple-mpi.f90:17
************************************************************************
1:#0  simple () at simple-mpi.f90:15

unrecognized command [made-up-command]. Type help to find out list of possible commands.
************************************************************************
1:Continuing.
1:
1:Thread 1 "simple-mpi.exe" hit Breakpoint 3, simple () at simple-mpi.f90:17
1:17  if (process_rank == 0) then

File [deliberately-missing-file.mdb] not found. Please check the file exists and try again.
unrecognized command [status]. Type help to find out list of possible commands.
0:$1 = 25
************************************************************************
1:$1 = 25

0:Continuing.
0: process 0 sleeping for 3s...
0:           1 s...
0:           2 s...
0:           3 s...
0: in level 1
0: in level 2
0: internal process:            0 of            2
0: var =    0.00000000    
0:[Thread 0x7ffff660b640 (LWP 43673) exited]
0:[Thread 0x7ffff6e0c640 (LWP 43670) exited]
0:[Inferior 1 (process 43665) exited normally]
************************************************************************
1:Continuing.
1: in level 1
1: in level 2
1: internal process:            1 of            2
1: var =    10.0000000    
1:[Thread 0x7ffff660b640 (LWP 43672) exited]
1:[Thread 0x7ffff6e0c640 (LWP 43671) exited]
1:[Inferior 1 (process 43664) exited normally]

************************************************************************


exiting mdb...
"""


def strip_runtime_specific_output(text: str) -> str:
    # remove process ids
    text = re.sub(r"process \d+", "process [proc id]", text)
    # remove LWP
    text = re.sub(r"(LWP \d+)", "(LWP XXX)", text)
    # remove thread ids
    text = re.sub(r"Thread \d+.\d+", "Thread [thread id]", text)
    # remove absolute cwd
    text = re.sub(r"cwd = '[\/\w]+'", "cwd = [mdb root]", text)
    # remove absolute exe
    text = re.sub(r"exe = '[\/\w]+/simple-mpi.exe'", "exe = simple-mpi.exe", text)
    # remove program address
    text = re.sub(r"at 0[xX][0-9a-fA-F]+:", "at [hex address]", text)
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


def test_mdb_simple() -> None:
    # kill any stray gdb sessions
    run(
        shlex.split("pkill gdb"),
        capture_output=True,
    )

    os.environ["MDB_LAUNCH_LOG_LEVEL"] = "DEBUG"

    # run the mdb launcher in the background
    Popen(
        shlex.split("mdb launch -b gdb -t examples/simple-mpi.exe -n 2"),
        stdin=None,
        stdout=None,
        stderr=None,
    )

    # create a simple mdb script for the test
    with open("integration.mdb", mode="w") as script:
        script.write(script_text)

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
    with open("answer.txt", "w") as outfile:
        outfile.write(result_txt)

    # remove run specific outputs
    result_txt = standardize_output(result_txt)

    assert result_txt == standardize_output(ans_text)


ans_text2 = """DEBUG:asyncio:Using selector: EpollSelector
INFO:root:Attempt 0 to connect to exchange server.
INFO:root:sleeping for 1s
INFO:root:Attempt 1 to connect to exchange server.
INFO:root:sleeping for 1s
INFO:root:Attempt 2 to connect to exchange server.
INFO:root:sleeping for 1s
INFO:root:Attempt 3 to connect to exchange server.
INFO:root:sleeping for 1s
INFO:root:Attempt 4 to connect to exchange server.
INFO:root:sleeping for 1s
INFO:root:Attempt 5 to connect to exchange server.
INFO:root:sleeping for 1s
INFO:root:Attempt 6 to connect to exchange server.
INFO:root:sleeping for 1s
INFO:root:Attempt 7 to connect to exchange server.
INFO:root:sleeping for 1s
INFO:root:Attempt 8 to connect to exchange server.
INFO:root:sleeping for 1s
INFO:root:Attempt 9 to connect to exchange server.
INFO:root:sleeping for 1s
ERROR:mdb.mdb_attach:couldn't connect to exchange server at localhost:2000.
"""


def test_mdb_timeout() -> None:

    os.environ["MDB_ATTACH_LOG_LEVEL"] = "DEBUG"

    # remove existing log file
    os.remove("mdb-attach.log")
    # run mdb attach without start mdb launch
    run(shlex.split("mdb attach"))

    with open("mdb-attach.log") as logfile:
        result_txt = "".join(logfile.readlines())

    assert result_txt == ans_text2
