# Copyright 2023-2024 Tom Meltzer. See the top-level COPYRIGHT file for
# details.

import json
from dataclasses import dataclass
from typing import Any

MDB_CLIENT = "mdb client"
DEBUG_CLIENT = "debug client"
EXCHANGE = "exchange server"

END_BYTES = b"_MDB_END_"


@dataclass
class Message:
    msg_type: str
    data: dict[str, Any]

    @staticmethod
    def from_json(text: bytes) -> "Message":
        msg = json.loads(text.decode()[: -len(END_BYTES)])
        return Message(msg["msg_type"], msg["data"])

    @staticmethod
    def debug_conn_request() -> "Message":
        return Message(
            "debug_conn_request",
            {"from": DEBUG_CLIENT, "to": EXCHANGE},
        )

    @staticmethod
    def debug_conn_response() -> "Message":
        return Message(
            "mdb_conn_response",
            {
                "from": EXCHANGE,
                "to": DEBUG_CLIENT,
            },
        )

    @staticmethod
    def mdb_conn_request() -> "Message":
        return Message(
            "mdb_conn_request",
            {"from": MDB_CLIENT, "to": EXCHANGE},
        )

    @staticmethod
    def mdb_conn_response(no_of_ranks: int, backend_name: str) -> "Message":
        return Message(
            "mdb_conn_response",
            {
                "from": EXCHANGE,
                "to": MDB_CLIENT,
                "no_of_ranks": no_of_ranks,
                "backend_name": backend_name,
            },
        )

    @staticmethod
    def mdb_command_request(command: str, select: list[int]) -> "Message":
        return Message(
            "mdb_command_request",
            {
                "from": MDB_CLIENT,
                "to": EXCHANGE,
                "command": command,
                "select": select,
            },
        )

    @staticmethod
    def mdb_interrupt_request() -> "Message":
        return Message(
            "mdb_interrupt_request",
            {
                "from": MDB_CLIENT,
                "to": EXCHANGE,
                "command": "interrupt",
            },
        )

    @staticmethod
    def debug_command_response(result: dict[int, str]) -> "Message":
        return Message(
            "debug_command_response",
            {
                "from": DEBUG_CLIENT,
                "to": EXCHANGE,
                "result": result,
            },
        )

    @staticmethod
    def exchange_command_response(messages: list["Message"]) -> "Message":
        results = {}
        for msg in messages:
            results.update(msg.data["result"])
        return Message(
            "exchange_command_response",
            {
                "from": EXCHANGE,
                "to": MDB_CLIENT,
                "results": results,
            },
        )

    def to_json(self) -> bytes:
        msg = dict(msg_type=self.msg_type, data=self.data)
        return json.dumps(msg).encode() + END_BYTES
