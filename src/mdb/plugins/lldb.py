from mdb.base import DebugBackend


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
