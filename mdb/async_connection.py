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
        msg = Message.from_json(await self.reader.readuntil(separator=END_BYTES))
        logger.debug("msg received [%s]", msg.msg_type)
        return msg

    async def send_message(self, msg: Message) -> None:
        self.writer.write(msg.to_json())
        logger.debug("sent message [%s]", msg.msg_type)
        return
