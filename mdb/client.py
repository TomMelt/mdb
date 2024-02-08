import asyncio
import json
import ssl
from os.path import expanduser

EXCHANGE_HOST = "127.0.0.1"
EXCHANGE_PORT = 8888
END_STR = "_MDB_END_"
PACKET_SIZE = 128

ctx = ssl.create_default_context(
    purpose=ssl.Purpose.SERVER_AUTH, cafile=expanduser("~/.mdb/cert.pem")
)
ctx.check_hostname = False


async def tcp_echo_client(message):
    print(f"sending: {message!r}")
    message = message + END_STR

    reader, writer = await asyncio.open_connection(
        EXCHANGE_HOST, EXCHANGE_PORT, ssl=ctx
    )

    writer.write(message.encode())
    await writer.drain()

    buffer = b""
    while True:
        data = await reader.read(PACKET_SIZE)
        if data[-len(END_STR) :] == END_STR.encode():
            buffer += data[: -len(END_STR)]
            break
        buffer += data
    response = buffer.decode()
    print(f"Received: {response!r}")

    writer.close()
    await writer.wait_closed()


command = {
    "command": "info",
    "version": "1.0.0",
    "destination": "mdb",
    "list": list(range(124)),
}

message = json.dumps(command)
asyncio.run(tcp_echo_client(message))
