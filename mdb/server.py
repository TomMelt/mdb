import asyncio
import ssl
from os.path import expanduser

EXCHANGE_HOST = "127.0.0.1"
EXCHANGE_PORT = 8888
END_STR = "_MDB_END_"
PACKET_SIZE = 128

ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(expanduser("~/.mdb/cert.pem"), expanduser("~/.mdb/key.rsa"))


async def handle_echo(reader, writer):
    buffer = b""
    while True:
        data = await reader.read(PACKET_SIZE)
        if data[-len(END_STR) :] == END_STR.encode():
            buffer += data[: -len(END_STR)]
            break
        buffer += data

    message = buffer.decode()
    addr = writer.get_extra_info("peername")

    print(f"Received {message!r} from {addr!r}")

    writer.write((message + END_STR).encode())
    await writer.drain()

    print("Close the connection")
    writer.close()
    await writer.wait_closed()


async def main():
    server = await asyncio.start_server(
        handle_echo,
        EXCHANGE_HOST,
        EXCHANGE_PORT,
        ssl=ctx,
    )

    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    print(f"Serving on {addrs}")

    async with server:
        await server.serve_forever()


asyncio.run(main())
