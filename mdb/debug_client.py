import asyncio
import logging

import pexpect

from .async_client import AsyncClient
from .backend import GDBBackend, LLDBBackend
from .utils import strip_bracketted_paste


class DebugClient(AsyncClient):
    def __init__(self, opts):
        super().__init__(opts=opts)
        self.myrank = int(opts["rank"])
        self.target = opts["target"]
        self.dbg_proc = None
        if opts["backend"].lower() == "gdb":
            self.backend = GDBBackend()
        elif opts["backend"].lower() == "lldb":
            self.backend = LLDBBackend()

    @property
    def my_type(self):
        info = {
            "type": "debug",
            "rank": self.myrank,
            "sockname": list(self.conn.writer.get_extra_info("sockname")),
            "version": "0.0.1",
        }
        return info

    async def init_debug_proc(self):
        backend = self.backend
        dbg_proc = pexpect.spawn(
            " ".join([backend.debug_command, self.target]), timeout=None
        )
        dbg_proc.expect(backend.prompt_string)
        for command in backend.start_commands:
            dbg_proc.sendline(command)
            await dbg_proc.expect(backend.prompt_string, async_=True)
        print(f"{backend.name} initialized")
        self.dbg_proc = dbg_proc

    def interact(self, message):
        if message["rank"] == self.myrank:
            logging.info(f"running interact mode on rank {self.myrank}.")
            self.dbg_proc.interact()

    async def wait_for_command(self):
        message = await self.conn.recv_message()
        command = message["command"]
        if command == "interrupt":
            print("HEEEEEEEEEEYYYYYYYYYYYYYYYYYY!!!!!!!!!!!")
        else:
            print("running command :: ", command)
            self.dbg_proc.sendline(command)
            await self.dbg_proc.expect(self.backend.prompt_string, async_=True)

            result = self.dbg_proc.before.decode()
            result = strip_bracketted_paste(result)

            message = {
                "result": result,
                "rank": self.myrank,
            }

            await self.conn.send_message(message)

    async def run(self):
        """
        Main loop of the asynchronous debugger wrapper.
        """
        await self.connect_to_exchange()
        await self.init_debug_proc()

        while True:
            logging.info(f"waiting for {self.backend} command...")
            await self.wait_for_command()


if __name__ == "__main__":
    opts = {
        "exchange_hostname": "localhost",
        "exchange_port": 2000,
        "backend": "gdb",
        "target": "examples/simple-mpi.exe",
    }
    client = DebugClient(opts)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.run())
    loop.close()
