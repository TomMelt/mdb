from abc import ABC, abstractmethod


class DebugBackend(ABC):
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


class GDBBackend(DebugBackend):
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
