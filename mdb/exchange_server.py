import asyncio
import ssl

from async_connection import AsyncConnection

from utils import ssl_cert_path, ssl_key_path


class AsyncExchangeServer:
    def __init__(self, opts):
        # fergus: pasted all the inherited attributes here
        self._init_tls()
        self.servers = []
        self.hostname = opts["hostname"]
        self.port = opts["port"]
        print(f"server started :: {self.hostname}:{self.port}")
        # fergus: added these
        self.socket = None

    def _init_tls(self):
        # fergus: i made no changes here other than paths
        print("using server tls")
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(
            ssl_cert_path(),
            ssl_key_path(),
        )
        self.context = context

    async def handle_connection(self, reader, writer):
        # fergus: what you probably want to do here is have a seperate
        # connection class that holds onto the connection reader/writer and
        # implements your handler methods

        print("Connection")

        # no try/except clause needed as the asyncio server does that for us
        conn = AsyncConnection(reader, writer)
        connection_type = await conn.handle_connection()

        # here you'd distinguish the connection too, to work out if it needs
        # to be pushed to `self.servers` or not, etc
        if connection_type == "debug":
            self.servers.append(conn)

        if connection_type == "client":
            command = await conn.recv_message()
            for server in self.servers:
                await server.send_message(command)
                response = await server.recv_message()
                await conn.send_message(response)

    def listen(self):
        # either pass in an event loop, or make one
        loop = asyncio.get_event_loop()

        task = asyncio.start_server(
            self.handle_connection,
            self.hostname,
            self.port,
            ssl=self.context,
        )

        loop.run_until_complete(task)
        loop.run_forever()


# from server import ExchangeServer

opts = {"hostname": "localhost", "port": 2000}
server = AsyncExchangeServer(opts=opts)
server.listen()
