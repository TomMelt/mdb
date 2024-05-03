import os
import shlex
from types import TracebackType
from typing import Generator, Optional, Type, Union
from subprocess import Popen, run, PIPE
from time import sleep

class BackgroundProcess:
    def __init__(self, command: str):
        self._running_command = None
        self.command = shlex.split(command)

    def __enter__(self) -> "BackgroundProcess":
        print("--- LAUNCHING ---")
        self._running_command = Popen(
            self.command,
            stdout=PIPE,
            stderr=PIPE,
            env={
                # on this CI this might run as root because
                # docker containers are the wild wild west
                "OMPI_ALLOW_RUN_AS_ROOT": "1",
                "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
                **os.environ,
            },
        )
        self._running_command.__enter__()
        sleep(2)
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        print("--- EXITING ---")
        # kill the background command
        self._running_command.kill()

        # print server's output
        print("--- OUTPUT BEGIN ---")
        print(self._running_command.stdout.read().decode())
        print("--- OUTPUT END ---")

        # print server's error log
        print("--- ERROR BEGIN ---")
        print(self._running_command.stderr.read().decode())
        print("--- ERROR END ---")

        self._running_command.__exit__(exc_type, exc_value, traceback)


