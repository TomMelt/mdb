# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import asyncio
import logging
import os
import ssl
from abc import ABC
from socket import gethostbyaddr
from typing import Any

from .async_connection import AsyncConnection
from .messages import Message
from .utils import ssl_cert_path, ssl_key_path

logger = logging.getLogger(__name__)


class AsyncClient(ABC):
    def __init__(self, opts: dict[Any, Any]):
        if not os.environ.get("MDB_DISABLE_TLS", None):
            self._init_tls()
        else:
            logger.warning("TLS is disabled by environment variable.")
            self.context = None

        self.exchange_hostname = opts["exchange_hostname"]
        self.exchange_port = opts["exchange_port"]
        self.connection_attempts = opts["connection_attempts"]

    def _init_tls(self) -> None:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_cert_chain(
            ssl_cert_path(),
            ssl_key_path(),
        )
        context.load_verify_locations(ssl_cert_path())

        # insecure debug mode
        if os.environ.get("MDB_DISABLE_HOSTNAME_VERIFY", None):
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        self.context = context

    async def init_connection(self) -> None:
        try:
            cert_host = gethostbyaddr(self.exchange_hostname)[0]
            reader, writer = await asyncio.open_connection(
                cert_host, self.exchange_port, ssl=self.context
            )
            self.conn = AsyncConnection(reader, writer)
        except Exception as e:
            logger.exception("init connection error")
            raise e

    async def connect_to_exchange(self, msg: "Message") -> "Message":
        attempts = 0
        while True:
            if attempts == self.connection_attempts:
                exception_msg = f"couldn't connect to exchange server at {self.exchange_hostname}:{self.exchange_port}."
                raise ConnectionError(exception_msg)
            try:
                await self.init_connection()
                logger.info("connected to exchange")
                await self.conn.send_message(msg)
                msg = await self.conn.recv_message()
                break
            except Exception as e:
                await asyncio.sleep(1)
                logger.exception("%s", e)
                logger.info("Attempt %d/%d to connect to exchange server. Sleeping 1 second...", attempts, self.connection_attempts)
                attempts += 1
        return msg

    async def close(self) -> None:
        self.conn.writer.close()
        await self.conn.writer.wait_closed()
