import asyncio
import ssl
from os.path import expanduser


class AsyncClient:
    def __init__(self, opts):
        # fergus: pasted all the inherited attributes here
        self._init_tls()
        self.servers = []
        self.hostname = opts["hostname"]
        self.port = opts["port"]
        print(f"client for {self.hostname}:{self.port}")
        self.end_str = "_MDB_END_"
        self.buffer_size = 128
        # fergus: added these
        self.socket = None

    def _init_tls(self):
        # fergus: i made no changes here other than paths
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_cert_chain(
            expanduser("../python-ssl/certs/cert.pem"),
            expanduser("../python-ssl/certs/key.rsa"),
        )
        # context.load_verify_locations(expanduser("../python-ssl/certs/cert.pem"))
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.context = context

    async def run(self):
        reader, writer = await asyncio.open_connection(
            self.hostname, self.port, ssl=self.context
        )

        writer.write("What's good?".encode())
        content = await reader.read(self.buffer_size)
        print("Got message: ", content.decode())


if __name__ == "__main__":
    opts = {"hostname": "localhost", "port": 2000}
    loop = asyncio.get_event_loop()
    client = AsyncClient(opts)
    loop.run_until_complete(client.run())
    loop.close()
