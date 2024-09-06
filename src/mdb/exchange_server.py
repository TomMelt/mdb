# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import asyncio
import logging
import os
import signal
import ssl
from typing import Any, Coroutine, Optional

from .async_connection import AsyncConnection
from .messages import DEBUG_CLIENT, MDB_CLIENT, Message
from .utils import ssl_cert_path, ssl_key_path

logger = logging.getLogger(__name__)


class AsyncExchangeServer:
    def __init__(self, opts: dict[str, Any]):

        self.context: Optional[ssl.SSLContext] = None

        if not os.environ.get("MDB_DISABLE_TLS", None):
            self._init_tls()
        else:
            logger.warning("TLS is disabled by environment variable.")

        self.number_of_ranks = opts["number_of_ranks"]
        self.hostname = opts["hostname"]
        self.port = opts["port"]
        self.backend_name = opts["backend"]
        self.launch_task = opts["launch_task"]
        self.debuggers: list[AsyncConnection] = []
        logger.info(f"echange server started :: {self.hostname}:{self.port}")

    def _init_tls(self) -> None:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(
            ssl_cert_path(),
            ssl_key_path(),
        )
        # add these two lines to force check of client credentials
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(ssl_cert_path())
        self.context = context

    async def handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        # no try/except clause needed as the asyncio server does that for us
        conn = AsyncConnection(reader, writer)
        try:
            msg = await conn.recv_message()
        except Exception as e:
            logger.exception("%s", e)
            return

        logger.info(
            "exchange server received [%s] from %s.",
            msg.msg_type,
            msg.data["from"],
        )

        # chekhov's loop
        loop = asyncio.get_event_loop()

        # here you'd distinguish the connection too, to work out if it needs
        # to be pushed to `self.debuggers` or not, etc

        if msg.data["from"] == DEBUG_CLIENT:
            self.debuggers.append(conn)
            await conn.send_message(Message.debug_conn_response())
            # wait for it to inform us that it's completed init
            init_message = await conn.recv_message()

            if init_message.msg_type != "debug_init_complete":
                logger.error(
                    "Client did not send initialize: received [%s]",
                    init_message.msg_type,
                )
            else:
                logger.info("Client sent initialization confirmed")

            return  # keep connection open

        if msg.data["from"] == MDB_CLIENT:
            # tell the client about the setup
            await conn.send_message(
                Message.mdb_conn_response(
                    no_of_ranks=self.number_of_ranks, backend_name=self.backend_name
                )
            )
            # schedule the loop to run
            loop.create_task(self.client_loop(conn))
            # but allow this function to return so it's not just stuck on the
            # stack
            return

        # do this incase we somehow fall through
        conn.writer.close()

    async def _forward_all_debuggers_to_client(self, conn: AsyncConnection) -> None:
        while True:
            tasks = [
                asyncio.create_task(debugger.recv_message())
                for debugger in self.debuggers
            ]
            messages = await asyncio.gather(*tasks)

            if all(i.msg_type == "debug_command_response" for i in messages):
                logger.debug("Sending results to client")
                await conn.send_message(
                    Message.exchange_command_response(messages=messages)
                )
            elif all(i.msg_type == "pong" for i in messages):
                logger.debug("Sending pong to client")
                await conn.send_message(Message.pong())
            else:
                logger.error(
                    "Inconsistent debugger message types: %s",
                    set(i.msg_type for i in messages),
                )

    async def client_loop(self, conn: AsyncConnection) -> None:
        # the problem here is we don't know if another message is going to come
        # from the client before the debugger has had the time to send
        # something back, and we can't assume all sends will be followed by
        # receives in order. It is valid for the client to make that
        # assumption, but not for the exchange server

        # to handle this, every time a message comes in from the client, we send it to all debuggers
        # every time a message comes in from the debuggers, we send it to the client

        asyncio.create_task(self._forward_all_debuggers_to_client(conn))

        while True:
            try:
                command = await conn.recv_message()
                logger.debug("Received from client: %s", command)
            except asyncio.exceptions.IncompleteReadError:
                logger.info("shutting down exchange server")
                await self.shutdown(signal.SIGINT.name)
                break
            for debugger in self.debuggers:
                await debugger.send_message(command)

    def start_server(self) -> Coroutine[Any, Any, Any]:
        task = asyncio.start_server(
            self.handle_connection,
            self.hostname,
            self.port,
            ssl=self.context,
        )
        return task

    def listen(self) -> None:
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

    async def shutdown(self, signame: str) -> None:
        """Cleanup tasks tied to the service's shutdown."""
        loop = asyncio.get_event_loop()
        logger.info(f"mdb launcher received signal {signame}")
        try:
            proc = self.launch_task.result()
            logger.info(f"terminating process [{proc.pid}]")
            proc.terminate()
            proc.kill()
            logger.info(f"process [{proc.pid}] terminated")
        except Exception as e:
            print(e)
        loop.stop()
