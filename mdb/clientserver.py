import json


class ClientServer:
    def __init__(self):
        self.end_str = "_MDB_END_"
        self.buffer_size = 128
        self._init_tls()
        self.ssl_sock = None

    def _init_tls(self):
        pass

    def send_message(self, message):
        # print(f"-> sending : {message}")
        message_str = json.dumps(message)
        message_str += self.end_str
        self.ssl_sock.send(message_str.encode())

    def recv_message(self):
        buffer = b""
        while True:
            data = self.ssl_sock.recv(self.buffer_size)
            if data[-len(self.end_str) :] == self.end_str.encode():
                buffer += data[: -len(self.end_str)]
                break
            buffer += data
        message_str = buffer.decode()
        message = json.loads(message_str)
        # print(f"-> received: {message}")
        return message
