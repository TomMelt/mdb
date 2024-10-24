import os
import shlex
from subprocess import PIPE, Popen
from time import sleep
from types import TracebackType
from typing import Any, Optional, Type


class BackgroundProcess:
    def __init__(self, command: str):
        self._running_command: Optional[Popen[Any]] = None
        self.command = shlex.split(command)

    def __enter__(self) -> "BackgroundProcess":
        self._running_command = Popen(
            self.command,
            stdout=PIPE,
            stderr=PIPE,
            env={
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
        if self._running_command is not None:
            print("--- EXITING ---")
            # kill the background command
            self._running_command.kill()

            # print server's output
            print("--- OUTPUT BEGIN ---")
            if self._running_command.stdout is not None:
                print(self._running_command.stdout.read().decode())
            print("--- OUTPUT END ---")

            # print server's error log
            print("--- ERROR BEGIN ---")
            if self._running_command.stderr is not None:
                print(self._running_command.stderr.read().decode())
            print("--- ERROR END ---")

            self._running_command.__exit__(exc_type, exc_value, traceback)
