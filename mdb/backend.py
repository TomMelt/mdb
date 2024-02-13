from abc import ABC, abstractmethod


class DebugBackend(ABC):
    def __init__(self):
        pass

    @property
    @abstractmethod
    def binary_name(self):
        pass

    @property
    @abstractmethod
    def prompt_string(self):
        pass


class GDBBackend(DebugBackend):
    @property
    def binary_name(self):
        return "gdb"

    @property
    def prompt_string(self):
        return r"\(gdb\)"


class LLVMBackend(DebugBackend):
    @property
    def binary_name(self):
        return "lldb"
