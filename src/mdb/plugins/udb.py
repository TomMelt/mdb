from mdb.backend import DebugBackend


class UDBBackend(DebugBackend):

    @property
    def name(self) -> str:
        return "udb"

    @property
    def debug_command(self) -> str:
        return "udb -q --defer-recording -iex 'set prompt -status (udb){space}'"

    @property
    def argument_separator(self) -> str:
        return "--args"

    @property
    def prompt_string(self) -> str:
        return r"\(udb\)"

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
