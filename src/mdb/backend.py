# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

from abc import ABC, abstractmethod
from typing import Dict, Type
import importlib.util
import os
import glob


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

    @abstractmethod
    def runtime_options(self, opts: dict[str, str]) -> list[str]:
        pass


backends: Dict[str, Type[DebugBackend]] = {}


def load_plugins() -> None:
    plugin_dir = os.path.join(os.path.dirname(__file__), "plugins")
    if not os.path.exists(plugin_dir):
        return  # no plugin exist

    for file in glob.glob(os.path.join(plugin_dir, "*.py")):
        module_name = os.path.splitext(os.path.basename(file))[0]
        spec = importlib.util.spec_from_file_location(module_name, file)
        if spec is None or spec.loader is None:  # handle None case
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # check if module defines a DebugBackend subclass, then store it in backends dictionary
        for attr in dir(module):
            cls = getattr(module, attr)
            if (
                isinstance(cls, type)
                and issubclass(cls, DebugBackend)
                and cls is not DebugBackend
            ):
                backends[cls().name] = cls


load_plugins()
