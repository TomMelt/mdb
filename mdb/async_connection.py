import asyncio
import json
import logging
import os


class AsyncConnection:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.type = ""
        self.end_bytes = b"_MDB_END_"
        self.debug = bool(int(os.environ.get("MDB_DEBUG_MESSAGES", 0)))

    async def recv_message(self):
        message = await self.reader.readuntil(separator=self.end_bytes)
        message = message[: -len(self.end_bytes)]
        message = json.loads(message.decode())
        logging.info(f"-> received: {message}")
        return message

    async def send_message(self, message):
        logging.info(f"-> sending : {message}")
        message = json.dumps(message).encode()
        message += self.end_bytes
        self.writer.write(message)

    async def handle_connection(self):
        message = await self.recv_message()
        try:
            self.type = message["type"]
        except KeyError:
            print("key [type] not found.")

        if self.type == "debug":
            logging.info(
                f'connection from {message["sockname"]} on rank {message["rank"]}'
            )
        elif self.type == "client":
            logging.info(f'connection from {message["sockname"]}')

        message = {"success": True}
        await self.send_message(message)
        return self.type
