from mdb.backend import DebugBackend


class GDBBackend(DebugBackend):

    @property
    def name(self) -> str:
        return "rust-gdb"

    @property
    def debug_command(self) -> str:
        return "rust-gdb -q"

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

    def runtime_options(self, opts: dict[str, str]) -> list[str]:
        return []
