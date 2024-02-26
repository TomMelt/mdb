import asyncio
import logging

logger = logging.getLogger(__name__)

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

        logger.debug("Selected backend: %s", self.backend.name)

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

        logger.debug("Backend init finished: %s", backend.name)
        self.dbg_proc = dbg_proc

    def interact(self, message):
        if message["rank"] == self.myrank:
            logger.info("Running interact mode on rank %s", self.myrank)
            self.dbg_proc.interact()

    async def execute_command(self, command, prev: asyncio.Task):
        if command == "interrupt":
            logger.warning("Interrupt received")
            # stop whatever is current running, so it doesn't try to reply
            success = prev.cancel()

            if not success:
                # nothing needed cancelling, so no reply needed
                logger.debug("No task to interrupt")
                return

            # send intterupt to the process
            self.dbg_proc.sendintr()
            await self.dbg_proc.expect(self.backend.prompt_string, async_=True)
            # report on how that all went
            reply = {
                "result": f"Interrupted: {success}",
                "rank": self.myrank,
            }

        else:
            logger.debug("Running command: '%s'", command)
            self.dbg_proc.sendline(command)
            await self.dbg_proc.expect(self.backend.prompt_string, async_=True)

            result = self.dbg_proc.before.decode()
            result = strip_bracketted_paste(result)
            reply = {
                "result": result,
                "rank": self.myrank,
            }

        logger.debug("Replying to: '%s'", command)
        await self.conn.send_message(reply)

    async def run(self):
        """
        Main loop of the asynchronous debugger wrapper.
        """
        await self.connect_to_exchange()
        await self.init_debug_proc()

        previous_task = None

        while True:
            # as soon as we get a command, run it so we can go back to waiting
            # for the next command (else we can't capture interrupts correctly)
            message = await self.conn.recv_message()
            previous_task = asyncio.create_task(
                self.execute_command(message["command"], previous_task)
            )


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
