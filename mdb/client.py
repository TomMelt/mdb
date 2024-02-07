import asyncio
import json
import ssl
from os.path import expanduser


async def tcp_echo_client(message):
    ctx = ssl.create_default_context(
        purpose=ssl.Purpose.SERVER_AUTH, cafile=expanduser("~/.mdb/cert.pem")
    )
    ctx.check_hostname = False
    reader, writer = await asyncio.open_connection("127.0.0.1", 8888, ssl=ctx)

    print(f"Send: {message!r}")
    writer.write(message.encode())
    await writer.drain()

    buffer = b""
    while True:
        data = await reader.read(100)
        if data[-3:] == b"EOF":
            buffer += data[:-3]
            break
        buffer += data
    response = buffer.decode()
    print(f"Received: {response!r}")

    print("Close the connection")
    writer.close()
    await writer.wait_closed()


command = {
    "command": "info",
    "version": "1.0.0",
    "destination": "mdb",
    "list": list(range(124)),
}

asyncio.run(tcp_echo_client(json.dumps(command) + "EOF"))
