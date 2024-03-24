# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import asyncio
import logging

from .messages import END_BYTES, Message

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
            raw_msg = await self.reader.readuntil(separator=END_BYTES)
        except Exception as e:
            logger.exception("async read error")
            raise e
        msg = Message.from_json(raw_msg)
        logger.debug("msg received [%s]", msg.msg_type)
        return msg

    async def send_message(self, msg: Message) -> None:
        try:
            self.writer.write(msg.to_json())
        except Exception as e:
            logger.exception("async send error")
            raise e
        logger.debug("sent message [%s]", msg.msg_type)
        return
