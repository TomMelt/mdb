# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

from __future__ import annotations

import logging
from typing import Any

from .async_client import AsyncClient
from .messages import Message

logger = logging.getLogger(__name__)


class Client(AsyncClient):
    def __init__(self, opts: dict[str, Any]):
        super().__init__(opts=opts)

    async def send_interrupt(self, signame: str) -> None:
        logger.info("Sending interrupt [%s]", signame)
        # interrupt will cause the debuggers to send back a status as to
        # whether interrupt was success, so we need to read that from the
        # message queue
        await self.conn.send_message(Message.mdb_interrupt_request())

    async def run_command(self, command: str, select: list[int]) -> "Message":
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
        self.backend_name = msg.data["backend_name"]
        return
