import os
import re
import shlex
from subprocess import Popen, run
from typing import Union

from mdb.utils import strip_bracketted_paste, strip_control_characters

script_text = """# this is a simple test script
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
!echo hello
broadcast start
p 5*5
broadcast stop
command continue
command quit
quit
"""

ans_text = """Connecting processes... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2/2
hello
mdb - mpi debugger - built on gdb. Type ? for more info. To exit interactive mode type "q", "quit", "Ctrl+D" or "Ctrl+]".
1:process 127650
1:cmdline = './examples/simple-mpi.exe'
1:cwd = '/home/melt/sync/cambridge/projects/side/mdb'
1:exe = '/home/melt/sync/cambridge/projects/side/mdb/examples/simple-mpi.exe'

0:process 127646
0:cmdline = './examples/simple-mpi.exe'
0:cwd = '/home/melt/sync/cambridge/projects/side/mdb'
0:exe = '/home/melt/sync/cambridge/projects/side/mdb/examples/simple-mpi.exe'

1:Breakpoint 2 at 0x5555555552da: file simple-mpi.f90, line 15.

0:Breakpoint 2 at 0x5555555552da: file simple-mpi.f90, line 15.

0:Breakpoint 3 at 0x5555555552f6: file simple-mpi.f90, line 17.

1:Breakpoint 3 at 0x5555555552f6: file simple-mpi.f90, line 17.

0:Continuing.
0:[New Thread 127646.127717]
0:[New Thread 127646.127719]
0:
0:Thread 1 "simple-mpi.exe" hit Breakpoint 2, simple () at simple-mpi.f90:15
0:15  var = 10.*process_rank

1:Continuing.
1:[New Thread 127650.127718]
1:[New Thread 127650.127720]
1:
1:Thread 1 "simple-mpi.exe" hit Breakpoint 2, simple () at simple-mpi.f90:15
1:15  var = 10.*process_rank

0:Continuing.
0:
0:Thread 1 "simple-mpi.exe" hit Breakpoint 3, simple () at simple-mpi.f90:17
0:17  if (process_rank == 0) then

0:#0  simple () at simple-mpi.f90:17

1:#0  simple () at simple-mpi.f90:15

unrecognized command [made-up-command]. Type help to find out list of possible commands.
1:Continuing.
1:
1:Thread 1 "simple-mpi.exe" received signal SIGINT, Interrupt.
1:simple () at simple-mpi.f90:15
1:15  var = 10.*process_rank

File [deliberately-missing-file.mdb] not found. Please check the file exists and try again.
0 1
0:$1 = 25

1:$1 = 25

0:Continuing.
0:
0:Thread 1 "simple-mpi.exe" received signal SIGINT, Interrupt.
0:simple () at simple-mpi.f90:17
0:17  if (process_rank == 0) then

1:Continuing.
1:
1:Thread 1 "simple-mpi.exe" received signal SIGINT, Interrupt.
1:simple () at simple-mpi.f90:15
1:15  var = 10.*process_rank

Closing processes... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2/2

exiting mdb...
"""


def strip_runtime_specific_output(text: str) -> str:
    # remove process ids
    text = re.sub(r"process \d+", "process [proc id]", text)
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
    # remove process and thread ids
    text = strip_runtime_specific_output(text)
    # sort output lines in alphabetical order
    text = "\n".join(sorted(text.splitlines()))

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

    # run the mdb launcher in the background
    Popen(
        shlex.split(
            "mdb launch -n 2 --launch-command='mpirun --oversubscribe' ./examples/simple-mpi.exe"
        ),
        stdin=None,
        stdout=None,
        stderr=None,
    )

    # create a simple mdb script for the test
    with open("integration.mdb", mode="w") as script:
        script.write(script_text)

    # run mdb attach and collect the stdout
    result = run(
        shlex.split("mdb attach -n 2 -x integration.mdb -b MAIN__"),
        capture_output=True,
    )

    os.remove("integration.mdb")

    # filter out the escape sequences
    result_txt = result.stdout.decode("utf-8")
    result_txt = strip_control_characters(strip_bracketted_paste(result_txt))
    result_txt = re.sub("\r", "", result_txt)
    result_txt = re.sub("\t", "", result_txt)

    # uncomment this block to write test output
    # with open("answer.txt", "w") as outfile:
    #     outfile.write(result_txt)

    # remove run specific outputs
    result_txt = standardize_output(result_txt)

    assert result_txt == standardize_output(ans_text)


ans_text2 = """Connecting processes...                                          0/2
error: mdb timeout with error message "localhost:2000: Connection timed out."
"""


def test_mdb_timeout() -> None:
    # run mdb attach without start mdb launch
    result = run(
        shlex.split("mdb attach -n 2 -b MAIN__"),
        capture_output=True,
    )

    result_txt = result.stdout.decode("utf-8")

    assert result_txt == ans_text2
