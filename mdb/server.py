import asyncio
import ssl
from os.path import expanduser


async def handle_echo(reader, writer):
    buffer = b""
    while True:
        data = await reader.read(100)
        if data[-3:] == b"EOF":
            buffer += data[:-3]
            break
        buffer += data
    message = buffer.decode()
    addr = writer.get_extra_info("peername")

    print(f"Received {message!r} from {addr!r}")

    print(f"Send: {message!r}")
    writer.write((message + "EOF").encode())
    await writer.drain()

    print("Close the connection")
    writer.close()
    await writer.wait_closed()


async def main():
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(expanduser("~/.mdb/cert.pem"), expanduser("~/.mdb/key.rsa"))
    server = await asyncio.start_server(
        handle_echo,
        "127.0.0.1",
        8888,
        ssl=ctx,
    )

    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    print(f"Serving on {addrs}")

    async with server:
        await server.serve_forever()


asyncio.run(main())
