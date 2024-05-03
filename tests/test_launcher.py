from utils import BackgroundProcess

from mdb.mdb_client import Client

import asyncio
import time

def test_ping_launcher() -> None:
    launch_command = "mdb launch -b gdb -t examples/simple-mpi-cpp.exe -n 2 -h 127.0.0.1 --log-level=DEBUG -p 62000"

    client_opts = {
        "exchange_hostname": "127.0.0.1",
        "exchange_port": 62000,
        "connection_attempts": 3,
    }
    client = Client(opts=client_opts)

    with BackgroundProcess(launch_command):
        asyncio.run(client.connect())

    assert client.backend_name == "gdb"


