# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

from abc import ABC, abstractmethod
from typing import List, Type


class DebugBackend(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def debug_command(self) -> str:
        pass

    @property
    @abstractmethod
    def argument_separator(self) -> str:
        pass

    @property
    @abstractmethod
    def prompt_string(self) -> str:
        pass

    @property
    @abstractmethod
    def default_options(self) -> list[str]:
        pass

    @property
    @abstractmethod
    def start_command(self) -> str:
        pass

    @property
    @abstractmethod
    def float_regex(self) -> str:
        pass


class GDBBackend(DebugBackend):

    @property
    def name(self) -> str:
        return "gdb"

    @property
    def debug_command(self) -> str:
        return "gdb -q"

    @property
    def argument_separator(self) -> str:
        return "--args"

    @property
    def prompt_string(self) -> str:
        return r"\(gdb\)"

    @property
    def default_options(self) -> list[str]:
        commands = ["set pagination off", "set confirm off"]
        return commands

    @property
    def start_command(self) -> str:
        return "start"

    @property
    def float_regex(self) -> str:
        return r"\d+ = ([+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)"


class LLDBBackend(DebugBackend):
    @property
    def name(self) -> str:
        return "lldb"

    @property
    def debug_command(self) -> str:
        return "lldb --source-quietly --no-use-colors"

    @property
    def argument_separator(self) -> str:
        return "--"

    @property
    def prompt_string(self) -> str:
        return r"\(lldb\)"

    @property
    def default_options(self) -> list[str]:
        return ["b main"]

    @property
    def start_command(self) -> str:
        return "run"

    @property
    def float_regex(self) -> str:
        return r"\d+ = ([+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)"


backends: List[Type[DebugBackend]] = [LLDBBackend, GDBBackend]
