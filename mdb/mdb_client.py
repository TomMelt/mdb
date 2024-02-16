# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

from __future__ import annotations

from .async_client import AsyncClient
from .utils import prepend_ranks

# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from .mdb_attach import Prog_opts

# def clear_stdout(self) -> None:
#     pass


class Client(AsyncClient):
    def __init__(self, opts):
        super().__init__(opts=opts)
        self.number_of_ranks = 0

    @property
    def my_type(self):
        info = {
            "type": "client",
            "sockname": list(self.conn.writer.get_extra_info("sockname")),
            "version": "0.0.1",
        }
        return info

    async def run_command(self, command):
        message = {
            "type": "client",
            "command": command,
            "version": "0.0.1",
        }
        await self.conn.send_message(message)

        response = await self.conn.recv_message()

        output = response["result"]
        output = sorted(output, key=lambda result: result["rank"])
        lines = []
        for result in output:
            lines.append(prepend_ranks(output=result["result"], rank=result["rank"]))
        combined_output = (72 * "*" + "\n").join(lines)
        print(combined_output)

    async def connect(self):
        """
        Connect to exchange server.
        """
        await self.connect_to_exchange()

    # async def run(self):
    #     """
    #     Main loop of the asynchronous client.
    #     """
    #     await self.connect_to_exchange()

    #     # get input, for now just example hard coded
    #     print("waiting for input")
    #     while True:
    #         inp = input("> ")
    #         if inp == "q":
    #             break
    #         await self.run_command(inp)
