# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import asyncio
import logging
import re
import shutil
from typing import Any, Optional

import pexpect  # type: ignore

from .async_client import AsyncClient
from .backend import backends
from .messages import Message
from .utils import strip_bracketted_paste

logger = logging.getLogger(__name__)


class DebugClient(AsyncClient):
    def __init__(self, opts: dict[str, str]):
        super().__init__(opts=opts)  # type: ignore
        self.myrank = int(opts["rank"])
        self.target = opts["target"]
        self.stdout = opts["redirect_stdout"]
        self.args = opts["args"]
        self.is_running = False

        backend_name = opts["backend"].lower()
        if backend_name in backends:
            self.backend = backends[backend_name]()
        else:
            raise ValueError(f"Debugger backend is not supported: {backend_name}")

        self.runtimeOptions = self.backend.runtime_options(opts=opts)

        logger.debug("Selected backend: %s", self.backend.name)

    async def init_debug_proc(self) -> None:
        backend = self.backend
        if self.args:
            args = " ".join(self.args)
        else:
            args = ""

        debug_command = " ".join(
            [backend.debug_command, backend.argument_separator, self.target, args]
        )
        logger.debug("running debug command: [%s]", debug_command)

        # Extract the actual command name (first word) to check if it exists
        command_name = backend.debug_command.split()[0]
        if not shutil.which(command_name):
            raise FileNotFoundError(
                f"Debugger command '{command_name}' not found.\n"
                f"Please ensure '{command_name}' is installed and available in your PATH."
            )

        dbg_proc = pexpect.spawn(debug_command, timeout=None)
        dbg_proc.expect(backend.prompt_string)
        self.runtimeOptions += backend.default_options
        for command in self.runtimeOptions:
            dbg_proc.sendline(command)
            logger.debug("running runtime command: [%s]", command)
            await dbg_proc.expect(backend.prompt_string, async_=True)
        command = self.backend.start_command
        if self.stdout is not None:
            command += f" >> {self.stdout}"
        dbg_proc.sendline(command)
        await dbg_proc.expect(backend.prompt_string, async_=True)

        logger.debug("Backend init finished: %s", backend.name)
        self.dbg_proc = dbg_proc

    async def execute_command(
        self, message: Message, prev: Optional[asyncio.Task[Any]]
    ) -> None:
        command = message.data["command"]
        output = ""
        if command == "interrupt" and self.is_running:
            logger.warning("Interrupt received")
            # stop whatever is current running, so it doesn't try to reply
            if prev is not None:
                success = prev.cancel()

            if not success:
                # nothing needed cancelling, so no reply needed
                logger.debug("No task to interrupt")
                output = f"\r\nInterrupted: {success}\r\n"
            else:
                # send intterupt to the process
                self.dbg_proc.sendintr()

            await self.dbg_proc.expect(self.backend.prompt_string, async_=True)
            # report on how that all went
            output = self.dbg_proc.before.decode()
            output = strip_bracketted_paste(output)
            output += f"\r\nInterrupted: {success}\r\n"

        else:
            self.is_running = True
            select = message.data["select"]
            logger.debug("Running command: '%s'", command)
            logger.debug("self.myrank = %d", self.myrank)
            if self.myrank in select:
                if not self.dbg_proc.closed:
                    if re.match(r"^\s*dump binary value\s.*", command):
                        command = re.sub(r"\$RANK\$", str(self.myrank), command)
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
        self.is_running = False
        await self.conn.send_message(Message.debug_command_response(result=result))

    async def run(self) -> None:
        """
        Main loop of the asynchronous debugger wrapper.
        """
        msg = await self.connect_to_exchange(Message.debug_conn_request())
        logger.info("connected to exchange")
        await self.init_debug_proc()
        logger.info("debug proc initialized")

        # tell the exhange server we are done with init
        await self.conn.send_message(Message.debug_init_complete())

        previous_task = None

        while True:
            # as soon as we get a command, run it so we can go back to waiting
            # for the next command (else we can't capture interrupts correctly)
            msg = await self.conn.recv_message()

            if msg.msg_type == "ping":
                logger.debug("Received ping")
                await self.conn.send_message(Message.pong())
            elif msg.msg_type == "mdb_command_request":
                previous_task = asyncio.create_task(
                    self.execute_command(msg, previous_task)
                )
            elif msg.msg_type == Message.mdb_interrupt_request().msg_type:
                logger.debug("received interrupt: %s", msg.msg_type)
                previous_task = asyncio.create_task(
                    self.execute_command(msg, previous_task)
                )
            else:
                logger.error("Unhandled message type: %s", msg.msg_type)
