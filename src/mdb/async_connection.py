# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import asyncio
import logging
from .messages import Message

logger = logging.getLogger(__name__)


class AsyncConnection:
    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        self.reader = reader
        self.writer = writer
        self.type = ""

    async def recv_message(self) -> "Message":
        try:
            length = await self.reader.readexactly(4)
            length = int.from_bytes(length, byteorder='big', signed=False)
            raw_msg = await self.reader.readexactly(length)
        except Exception as e:
            logger.exception("async read error")
            raise e
        msg = Message.from_json(raw_msg)
        logger.debug("msg received [%s]", msg.msg_type)
        return msg

    async def send_message(self, msg: Message) -> None:
        try:
            data = msg.to_json()
            length_header = data.__len__().to_bytes(4, byteorder='big', signed=False)
            
            self.writer.write(length_header)
            self.writer.write(data)
            await self.writer.drain()

        except Exception as e:
            logger.exception("async send error")
            raise e
        logger.debug("sent message [%s]", msg.msg_type)
        return
