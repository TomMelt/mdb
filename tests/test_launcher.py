import asyncio
import shlex
from subprocess import run
from time import sleep
from typing import Generator

import pytest
from utils import BackgroundProcess

from mdb.mdb_client import Client


# todo: i forget how to do it but there's a
# universal pytest file you can define which
# contains fixtures to run for every test
@pytest.fixture(autouse=True)
def slow_down_tests() -> Generator[None, None, None]:
    yield
    sleep(1)
    run(
        shlex.split("pkill -9 mdb"),
        capture_output=True,
    )


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
