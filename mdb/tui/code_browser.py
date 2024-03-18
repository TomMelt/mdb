"""
Code browser example.

Run with:

    python code_browser.py PATH
"""

from rich.syntax import Syntax
from rich.text import Text
from rich.traceback import Traceback
from textual import on
from textual.app import App, Binding, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import (  # TextArea,
    Footer,
    Input,
    Label,
    RichLog,
    Static,
    TabbedContent,
    TabPane,
)


class CodeBrowser(App):
    """Textual code browser app."""

    CSS_PATH = "code_browser.tcss"
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding(
            "ctrl+c", "send_interrupt", "Send an interrupt", show=False, priority=True
        ),
    ]

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        with Container():
            with VerticalScroll(id="code-view"):
                yield Static(id="code", expand=True)
            yield RichLog(id="mdb_output")
            yield Input(placeholder="command", id="mdb_command_prompt")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#mdb_command_prompt").focus()

    @on(Input.Submitted)
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Called when the user click a file in the directory tree."""
        event.stop()
        code_view = self.query_one("#code", Static)
        TEXT = "where\r\n#0  \x1b[34m0x00007ffff7b207f8\x1b[m in \x1b[33m__GI___clock_nanosleep\x1b[m (\x1b[36mclock_id=clock_id@entry\x1b[m=0, \x1b[36mflags=flags@entry\x1b[m=0, \x1b[36mreq=req@entry\x1b[m=0x7fffffff7eb0, \x1b[36mrem=rem@entry\x1b[m=0x0) at \x1b[32m../sysdeps/u nix/sysv/linux/clock_nanosleep.c\x1b[m:78\r\n#1 \x1b[34m0x00007ffff7b25677\x1b[m in \x1b[33m__GI___nanosleep\x1b[m (\x1b[36mreq=req@entry\x1b[m=0x7fffffff7eb0, \x1b[36mrem=rem@entry\x1b[m=0x0) at \x1b[32m../sysdeps/unix/sysv/linux/nanosleep.c\x1b[m:25\r\n#2 \x1b[34m0x0000 7ffff7b56d3f\x1b[m in \x1b[33musleep\x1b[m (\x1b[36museconds\x1b[m=<optimised out>) at \x1b[32m../sysdeps/posix/usleep.c\x1b[m:31\r\n#3 \x1b[34m0x00007ffff7994768\x1b[m in \x1b[33mompi_mpi_init\x1b[m () from \x1b[32mtarget:/software/spack/opt/spack/linux-ubuntu22.04-skylak e/gcc-11.4.0/openmpi-4.1.5-3xx56go6lrswf72pghjz73xunrkkv47w/lib/libmpi.so.40\x1b[m\r\n#4 \x1b[34m0x00007ffff77d4602\x1b[m in \x1b[33mPMPI_Init\x1b[m () from \x1b[32mtarget:/software/spack/opt/spack/linux-ubuntu22.04-skylake/gcc-11.4.0/openmpi-4.1.5-3xx56go6lrswf72pghjz73xu nrkkv47w/lib/libmpi.so.40\x1b[m\r\n#5 \x1b[34m0x00007ffff7fa288c\x1b[m in \x1b[33mpmpi_init__\x1b[m () from \x1b[32mtarget:/software/spack/opt/spack/linux-ubuntu22.04-skylake/gcc-11.4.0/openmpi-4.1.5-3xx56go6lrswf72pghjz73xunrkkv47w/lib/libmpi_mpifh.so.40\x1b[m\r\n#6 \x1b [34m0x00005555555552c2\x1b[m in \x1b[33mhello_world_mpi\x1b[m () at \x1b[32mhello.f90\x1b[m:12\r\n"
        TEXT = TEXT * 4
        text_log = self.query_one(RichLog)
        text_log.write(Text.from_ansi(TEXT))
        try:
            syntax = Syntax.from_path(
                str("../../examples/simple-mpi.f90"),
                line_numbers=True,
                word_wrap=False,
                indent_guides=True,
                theme="github-dark",
            )
        except Exception:
            code_view.update(Traceback(theme="github-dark", width=None))
            self.sub_title = "ERROR"
        else:
            code_view.update(syntax)
            self.query_one("#code-view").scroll_home(animate=False)
            self.sub_title = str(event.value)

    def send_interrupt():
        pass


if __name__ == "__main__":
    CodeBrowser().run()
