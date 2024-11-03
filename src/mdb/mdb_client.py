# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

from __future__ import annotations

import logging

from .async_client import AsyncClient, AsyncClientOpts
from .messages import Message

logger = logging.getLogger(__name__)

# alias
ClientOpts = AsyncClientOpts


class Client(AsyncClient):
    def __init__(self, opts: AsyncClientOpts):
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

        while True:
            command_response = await self.conn.recv_message()

            if command_response.msg_type == "exchange_command_response":
                return command_response
            elif command_response.msg_type == "exchange_info":
                print(
                    "[*] Exchange Server: {}".format(command_response.data["message"])
                )
            else:
                raise Exception(
                    "Unhandled message type: {}".format(command_response.msg_type)
                )

    async def connect(self) -> None:
        """
        Connect to exchange server.
        """
        msg = await self.connect_to_exchange(Message.mdb_conn_request())
        self.number_of_ranks = msg.data["no_of_ranks"]
        self.backend_name = msg.data["backend_name"]
        self.select_str = msg.data["select_str"]
        return
