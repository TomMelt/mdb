# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import asyncio
import logging
from typing import Any, Optional

import pexpect  # type: ignore

from .async_client import AsyncClient
from .backend import DebugBackend, GDBBackend, LLDBBackend
from .messages import Message
from .utils import strip_bracketted_paste

logger = logging.getLogger(__name__)


class DebugClient(AsyncClient):
    def __init__(self, opts: dict[str, Any]):
        super().__init__(opts=opts)
        self.myrank = int(opts["rank"])
        self.target = opts["target"]
        self.args = opts["args"]
        if opts["backend"].lower() == "gdb":
            self.backend: DebugBackend = GDBBackend()
        elif opts["backend"].lower() == "lldb":
            self.backend = LLDBBackend()

        logger.debug("Selected backend: %s", self.backend.name)

    async def init_debug_proc(self) -> None:
        backend = self.backend
        if self.args:
            args = " ".join(self.args)
        else:
            args = ""

        print("backend.debug_command = ", backend.debug_command)
        print("backend.argument_separator = ", backend.argument_separator)
        print("self.target = ", self.target)
        print("args = ", args)
        debug_command = " ".join(
            [backend.debug_command, backend.argument_separator, self.target, args]
        )
        logger.debug("running debug command: [%s]", debug_command)
        dbg_proc = pexpect.spawn(debug_command, timeout=None)
        dbg_proc.expect(backend.prompt_string)
        for command in backend.start_commands:
            dbg_proc.sendline(command)
            await dbg_proc.expect(backend.prompt_string, async_=True)

        logger.debug("Backend init finished: %s", backend.name)
        self.dbg_proc = dbg_proc

    async def execute_command(
        self, message: Message, prev: Optional[asyncio.Task[Any]]
    ) -> None:
        command = message.data["command"]
        output = ""
        if command == "interrupt":
            logger.warning("Interrupt received")
            # stop whatever is current running, so it doesn't try to reply
            if prev is not None:
                success = prev.cancel()

            if not success:
                # nothing needed cancelling, so no reply needed
                logger.debug("No task to interrupt")

            # send intterupt to the process
            self.dbg_proc.sendintr()
            await self.dbg_proc.expect(self.backend.prompt_string, async_=True)
            # report on how that all went
            output = self.dbg_proc.before.decode()
            output = strip_bracketted_paste(output)
            output += f"\r\nInterrupted: {success}\r\n"

        else:
            select = message.data["select"]
            logger.debug("Running command: '%s'", command)
            logger.debug("self.myrank = %d", self.myrank)
            if self.myrank in select:
                if not self.dbg_proc.closed:
                    self.dbg_proc.sendline(command)
                    logger.debug("command running: '%s'", command)
                    await self.dbg_proc.expect(
                        [self.backend.prompt_string, pexpect.EOF], async_=True
                    )
                    output = self.dbg_proc.before.decode()
                    output = strip_bracketted_paste(output)
                    result = {self.myrank: output}
                else:
                    output = "\r\nDebug process is closed. Please re-launch mdb.\r\n"

        result = {self.myrank: output}
        await self.conn.send_message(Message.debug_command_response(result=result))

    async def run(self) -> None:
        """
        Main loop of the asynchronous debugger wrapper.
        """
        msg = await self.connect_to_exchange(Message.debug_conn_request())
        logger.info("connected to exchange")
        await self.init_debug_proc()
        logger.info("debug proc initialized")

        previous_task = None

        while True:
            # as soon as we get a command, run it so we can go back to waiting
            # for the next command (else we can't capture interrupts correctly)
            msg = await self.conn.recv_message()
            previous_task = asyncio.create_task(
                self.execute_command(msg, previous_task)
            )
