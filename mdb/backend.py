# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

from abc import ABC, abstractmethod

# main_list = [sdsdasd asdasd]

# def register_backend(backend):
#     main_list.append(backend)

# add getter function for main_list
# add setter function for main_list (register)


class DebugBackend(ABC):
    # name: str

    def __init__(self):
        pass

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def debug_command(self):
        pass

    @property
    @abstractmethod
    def prompt_string(self):
        pass

    @property
    @abstractmethod
    def start_commands(self):
        pass

    @property
    @abstractmethod
    def float_regex(self):
        pass


class GDBBackend(DebugBackend):
    # name = "gdb"

    @property
    def name(self):
        return "gdb"

    @property
    def debug_command(self):
        return "gdb -q "

    @property
    def prompt_string(self):
        return r"\(gdb\)"

    @property
    def start_commands(self):
        commands = ["set pagination off", "set confirm off", "start"]
        return commands

    @property
    def float_regex(self):
        return r"\d+ = ([+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)"


class LLDBBackend(DebugBackend):
    @property
    def name(self):
        return "lldb"

    @property
    def debug_command(self):
        return "lldb"

    @property
    def prompt_string(self):
        return r"\(lldb\)"

    @property
    def start_commands(self):
        commands = []
        return commands

    @property
    def float_regex(self):
        raise NotImplementedError
