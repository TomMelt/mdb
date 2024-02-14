import asyncio

import pexpect
from async_client import AsyncClient
from backend import GDBBackend
from utils import strip_bracketted_paste


class DebugClient(AsyncClient):
    def __init__(self, opts):
        super().__init__(opts=opts)
        self.myrank = opts["rank"]
        self.target = opts["target"]
        self.dbg_proc = None
        if opts["backend"].lower() == "gdb":
            self.backend = GDBBackend()

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

    async def wait_for_command(self):
        message = await self.conn.recv_message()
        command = message["command"]
        print("running command :: ", command)
        self.dbg_proc.sendline(command)
        await self.dbg_proc.expect(self.backend.prompt_string, async_=True)

        result = self.dbg_proc.before.decode()
        result = strip_bracketted_paste(result)

        await self.conn.send_message(dict(result=result))

    async def run(self):
        """
        Main loop of the asynchronous debugger wrapper.
        """
        await self.connect_to_exchange()
        await self.init_debug_proc()
        await self.wait_for_command()
        await self.close()


if __name__ == "__main__":
    opts = {
        "exchange_hostname": "localhost",
        "exchange_port": 2000,
        "rank": 1,
        "backend": "gdb",
        "target": "examples/simple-mpi.exe",
    }
    client = DebugClient(opts)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.run())
    loop.close()
