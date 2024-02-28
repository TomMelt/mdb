# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import asyncio
import logging
import ssl
import sys

from .async_connection import AsyncConnection
from .utils import ssl_cert_path, ssl_key_path

logger = logging.getLogger(__name__)


class AsyncExchangeServer:
    def __init__(self, opts):
        self._init_tls()
        self.number_of_ranks = opts["number_of_ranks"]
        self.hostname = opts["hostname"]
        self.port = opts["port"]
        self.backend = opts["backend"]
        self.servers = []
        logger.info(f"echange server started :: {self.hostname}:{self.port}")

    def _init_tls(self):
        # fergus: i made no changes here other than paths
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(
            ssl_cert_path(),
            ssl_key_path(),
        )
        # add these two lines to force check of client credentials
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(ssl_cert_path())
        self.context = context

    async def handle_connection(self, reader, writer):
        # fergus: what you probably want to do here is have a seperate
        # connection class that holds onto the connection reader/writer and
        # implements your handler methods

        # no try/except clause needed as the asyncio server does that for us
        conn = AsyncConnection(reader, writer)
        connection_type = await conn.handle_connection()
        logger.info(f"exchange server received a {connection_type} connection.")

        # checkhov's loop
        loop = asyncio.get_event_loop()

        # here you'd distinguish the connection too, to work out if it needs
        # to be pushed to `self.servers` or not, etc
        if connection_type == "debug":
            self.servers.append(conn)
            return  # keep connection open

        if connection_type == "client":
            # tell the client about the setup
            message = {
                "ranks": self.number_of_ranks,
                "backend": self.backend,
            }
            await conn.send_message(message)
            # schedule the loop to run
            loop.create_task(self.client_loop(conn))
            # but allow this function to return so it's not just stuck on the
            # stack
            return

        # do this incase we somehow fall through
        conn.writer.close()

    async def _forward_all_debuggers_to_client(self, conn):
        while True:
            tasks = [
                asyncio.create_task(debugger.recv_message())
                for debugger in self.servers
            ]
            output = await asyncio.gather(*tasks)
            response = {"result": output}
            logger.debug("Sending results to client")
            await conn.send_message(response)

    async def client_loop(self, conn):
        # the problem here is we don't know if another message is going to come
        # from the client before the debugger has had the time to send
        # something back, and we can't assume all sends will be followed by
        # receives in order. It is valid for the client to make that
        # assumption, but not for the exchange server

        # to handle this, every time a message comes in from the client, we send it to all debuggers
        # every time a message comes in from the debuggers, we send it to the client

        asyncio.create_task(self._forward_all_debuggers_to_client(conn))

        while True:
            command = await conn.recv_message()
            logger.debug("Received from client: %s", command)
            for debugger in self.servers:
                await debugger.send_message(command)

    def start_server(self):
        task = asyncio.start_server(
            self.handle_connection,
            self.hostname,
            self.port,
            ssl=self.context,
        )
        return task

    def listen(self):
        # either pass in an event loop, or make one
        loop = asyncio.get_event_loop()

        # TODO: to get better control of the server, we can wrap our own
        # transport layer and then add a system of hooks for logging or other
        # events. For example, if a debug client loses connection, the exchange
        # server should let the user know somehow. By using the library
        # `start_server`, we lose some of that control, but lets us move
        # faster.
        task = asyncio.start_server(
            self.handle_connection,
            self.hostname,
            self.port,
            ssl=self.context,
        )

        loop.run_until_complete(task)
        loop.run_forever()
