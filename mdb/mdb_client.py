# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

from __future__ import annotations

from .async_client import AsyncClient
from .utils import prepend_ranks


class Client(AsyncClient):
    def __init__(self, opts):
        super().__init__(opts=opts)
        self.number_of_ranks = 0
        self.backend = None

    @property
    def my_type(self):
        info = {
            "type": "client",
            "sockname": list(self.conn.writer.get_extra_info("sockname")),
            "version": "0.0.1",
        }
        return info

    async def send_interrupt(self, signame):
        print("Sending ", signame)
        # interrupt will cause the debuggers to send back a status as to
        # whether interrupt was success, so we need to read that from the
        # message queue
        await self.send_command("interrupt")

    async def send_command(self, command):
        message = {
            "type": "client",
            "command": command,
            "version": "0.0.1",
        }
        await self.conn.send_message(message)

    def handle_response(self, response):
        output = response["result"]
        output = sorted(output, key=lambda result: result["rank"])
        lines = []
        for result in output:
            lines.append(prepend_ranks(output=result["result"], rank=result["rank"]))
        combined_output = (72 * "*" + "\n").join(lines)
        # actually do the output
        print(combined_output)

    async def run_command(self, command):
        await self.send_command(command)
        response = await self.conn.recv_message()
        self.handle_response(response)

    async def connect(self):
        """
        Connect to exchange server.
        """
        await self.connect_to_exchange()
        message = await self.conn.recv_message()
        self.number_of_ranks = message["ranks"]
        self.backend = message["backend"]
