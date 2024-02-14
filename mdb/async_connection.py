import asyncio
import json


class AsyncConnection:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.type = ""
        self.end_bytes = b"_MDB_END_"

    async def recv_message(self):
        message = await self.reader.readuntil(separator=self.end_bytes)
        message = message[: -len(self.end_bytes)]
        message = json.loads(message.decode())
        print(f"-> received: {message}")
        return message

    async def send_message(self, message):
        print(f"-> sending : {message}")
        message = json.dumps(message).encode()
        message += self.end_bytes
        self.writer.write(message)

    async def handle_connection(self):
        message = await self.recv_message()
        try:
            self.type = message["type"]
        except KeyError:
            print("key [type] not found.")

        message = {"success": True}
        await self.send_message(message)
        return self.type
