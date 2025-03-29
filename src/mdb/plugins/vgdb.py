from mdb.backend import DebugBackend


class VGDBBackend(DebugBackend):
    @property
    def name(self) -> str:
        return "vgdb"

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
        return [
            "set pagination off",
            "set confirm off",
            "set sysroot /",
            "target extended-remote | vgdb --multi --vargs -q"
        ]

    @property
    def start_command(self) -> str:
        return "start"

    @property
    def float_regex(self) -> str:
        return r"\d+ = ([+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)"

    def runtime_options(self, opts:dict[str, str]) -> list[str]:
        return [
            f"set remote exec-file {opts["target"]}"
        ]