# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import asyncio
import logging
import os
import ssl
from abc import ABC, abstractmethod

from .async_connection import AsyncConnection
from .messages import Message
from .utils import ssl_cert_path, ssl_key_path

logger = logging.getLogger(__name__)


class AsyncClient(ABC):
    def __init__(self, opts):
        self._init_tls()
        self.exchange_hostname = opts["exchange_hostname"]
        self.exchange_port = opts["exchange_port"]
        self.conn = None

    def _init_tls(self):
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

    async def init_connection(self):
        reader, writer = await asyncio.open_connection(
            self.exchange_hostname, self.exchange_port, ssl=self.context
        )
        self.conn = AsyncConnection(reader, writer)

    async def connect_to_exchange(self, msg: "Message") -> "Message":
        status = False
        attempts = 0
        while not status:
            if attempts == 10:
                msg = f"couldn't connect to exchange server at {self.exchange_hostname}:{self.exchange_port}."
                raise ConnectionError(msg)
            try:
                await self.init_connection()
                logger.info("connected to exchange")
                await self.conn.send_message(msg)
                msg = await self.conn.recv_message()
                return msg
            except ConnectionRefusedError:
                await asyncio.sleep(1)
                logging.info(f"Attempt {attempts} to connect to exchange server.")
                logging.info("sleeping for 1s")
                attempts += 1

    async def close(self):
        self.conn.writer.close()
        await self.conn.writer.wait_closed()
