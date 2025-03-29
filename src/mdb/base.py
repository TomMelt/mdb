
from abc import ABC, abstractmethod
from typing import Dict, Type


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

    def runtime_options(self, opts: dict[str, str]) -> list[str]:
        return []
