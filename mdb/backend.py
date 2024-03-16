# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

from abc import ABC, abstractmethod


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
    def prompt_string(self) -> str:
        pass

    @property
    @abstractmethod
    def start_commands(self) -> list[str]:
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
        return "gdb -q "

    @property
    def prompt_string(self) -> str:
        return r"\(gdb\)"

    @property
    def start_commands(self) -> list[str]:
        commands = ["set pagination off", "set confirm off", "start"]
        return commands

    @property
    def float_regex(self) -> str:
        return r"\d+ = ([+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)"


class LLDBBackend(DebugBackend):
    @property
    def name(self) -> str:
        return "lldb"

    @property
    def debug_command(self) -> str:
        return "lldb"

    @property
    def prompt_string(self) -> str:
        return r"\(lldb\)"

    @property
    def start_commands(self) -> list[str]:
        raise NotImplementedError

    @property
    def float_regex(self) -> str:
        raise NotImplementedError


backends = [LLDBBackend, GDBBackend]
