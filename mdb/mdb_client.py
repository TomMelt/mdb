# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

from __future__ import annotations

from .async_client import AsyncClient
from .messages import Message


class Client(AsyncClient):
    def __init__(self, opts):
        super().__init__(opts=opts)
        self.number_of_ranks = 0
        self.backend = None

    async def send_interrupt(self, signame):
        print("Sending ", signame)
        # interrupt will cause the debuggers to send back a status as to
        # whether interrupt was success, so we need to read that from the
        # message queue
        await self.send_command("interrupt")

    async def send_command(self, command, select=None):
        message = {
            "type": "client",
            "select": select,
            "command": command,
        }
        await self.conn.send_message(message)

    async def run_command(self, command, select) -> "Message":
        await self.conn.send_message(
            Message.mdb_command_request(command=command, select=select)
        )
        command_response = await self.conn.recv_message()
        return command_response

    async def connect(self) -> None:
        """
        Connect to exchange server.
        """
        msg = await self.connect_to_exchange(Message.mdb_conn_request())
        self.number_of_ranks = msg.data["no_of_ranks"]
        self.backend = msg.data["backend"]
        return
