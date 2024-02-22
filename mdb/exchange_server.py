import asyncio
import logging
import ssl

from .async_connection import AsyncConnection
from .utils import ssl_cert_path, ssl_key_path


class AsyncExchangeServer:
    def __init__(self, opts):
        # fergus: pasted all the inherited attributes here
        self._init_tls()
        self.number_of_ranks = opts["number_of_ranks"]
        self.hostname = opts["hostname"]
        self.port = opts["port"]
        self.backend = opts["backend"]
        self.servers = []
        logging.info(f"echange server started :: {self.hostname}:{self.port}")

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
        logging.info(f"exchange server received a {connection_type} connection.")

        # here you'd distinguish the connection too, to work out if it needs
        # to be pushed to `self.servers` or not, etc
        if connection_type == "debug":
            self.servers.append(conn)
            return  # keep connection open

        async def temp(server):
            await server.send_message(command)
            message = await server.recv_message()
            return message

        if connection_type == "client":
            message = {
                "ranks": self.number_of_ranks,
                "backend": self.backend,
            }
            await conn.send_message(message)
            while True:
                command = await conn.recv_message()
                tasks = [asyncio.create_task(temp(server)) for server in self.servers]
                print("waiting for output...")
                output = await asyncio.gather(*tasks)
                print("Output received...")
                response = {"result": output}
                await conn.send_message(response)

        # do this incase we somehow fall through
        conn.writer.close()

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
