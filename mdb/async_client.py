import asyncio
import ssl
from os.path import expanduser

import pexpect
from clientserver import AsyncConnection


class AsyncClient:
    def __init__(self, opts):
        # fergus: pasted all the inherited attributes here
        self._init_tls()
        self.servers = []
        self.hostname = opts["hostname"]
        self.port = opts["port"]
        print(f"client for {self.hostname}:{self.port}")
        self.end_bytes = b"_MDB_END_"
        self.buffer_size = 128
        # fergus: added these
        self.conn = None
        self.myrank = opts["rank"]
        self.dbg_proc = None

    def _init_tls(self):
        # fergus: i made no changes here other than paths
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_cert_chain(
            expanduser("~/.mdb/cert.pem"),
            expanduser("~/.mdb/key.rsa"),
        )
        context.load_verify_locations(expanduser("~/.mdb/cert.pem"))
        # context.check_hostname = False
        # context.verify_mode = ssl.CERT_NONE
        self.context = context

    async def init_connection(self):
        reader, writer = await asyncio.open_connection(
            self.hostname, self.port, ssl=self.context
        )

        self.conn = AsyncConnection(reader, writer)

    async def report_to_exchange(self):
        await self.init_connection()

        message = {
            "type": "debug",
            "rank": self.myrank,
            "sockname": list(self.conn.writer.get_extra_info("sockname")),
            "version": "0.0.1",
        }

        await self.conn.send_message(message)
        message = await self.conn.recv_message()

        print("message = \n", message)

    def init_debug_proc(self):
        """
        initialize pexpect debug process
        """
        dbg_proc = pexpect.spawn("gdb -q", timeout=None)
        dbg_proc.expect(self.prompt)
        dbg_proc.sendline("set pagination off")
        dbg_proc.expect(self.prompt)
        dbg_proc.sendline("set confirm off")
        dbg_proc.expect(self.prompt)
        dbg_proc.sendline("start")
        dbg_proc.expect(self.prompt)
        self.dbg_proc = dbg_proc

    async def wait_for_command(self):
        message = await self.conn.recv_message()

        await self.conn.send_message(message)
        print("Got message: ", message)

    async def close(self):
        self.conn.writer.close()
        await self.conn.writer.wait_closed()


if __name__ == "__main__":
    opts = {"hostname": "localhost", "port": 2000, "rank": 1}
    client = AsyncClient(opts)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.report_to_exchange())
    loop.run_until_complete(client.wait_for_command())
    loop.run_until_complete(client.close())
    loop.close()
