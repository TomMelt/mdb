import os

import asyncio
import ssl
from abc import ABC, abstractmethod

from async_connection import AsyncConnection

from utils import ssl_cert_path, ssl_key_path


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

    @property
    @abstractmethod
    def my_type(self):
        pass

    async def connect_to_exchange(self):
        await self.init_connection()
        await self.conn.send_message(self.my_type)
        message = await self.conn.recv_message()
        if message["success"]:
            return
        else:
            msg = f"Failed to connect to exchange server at {self.exchange_hostname}:{self.exchange_port}."
            raise ConnectionError(msg)

    async def close(self):
        self.conn.writer.close()
        await self.conn.writer.wait_closed()


class mdbClient(AsyncClient):
    def __init__(self, opts):
        super().__init__(opts=opts)

    @property
    def my_type(self):
        info = {
            "type": "client",
            "sockname": list(self.conn.writer.get_extra_info("sockname")),
            "version": "0.0.1",
        }
        return info

    async def run_command(self, command):
        message = {
            "type": "client",
            "command": command,
            "version": "0.0.1",
        }
        await self.conn.send_message(message)

        message = await self.conn.recv_message()
        print(message["result"])

    async def run(self):
        """
        Main loop of the asynchronous client.
        """
        await self.connect_to_exchange()

        # get input, for now just example hard coded
        await self.run_command("info proc")

        # then at the end maybe close? this isn't essential since we can also
        # just let the socket drop and it will clean itself up
        await self.close()


if __name__ == "__main__":
    opts = {
        "exchange_hostname": "localhost",
        "exchange_port": 2000,
        "rank": 1,
        "backend": "gdb",
        "target": "examples/simple-mpi.exe",
    }
    client = mdbClient(opts)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.run())
    loop.close()
