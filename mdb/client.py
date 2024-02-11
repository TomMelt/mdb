import socket
import ssl
from os.path import expanduser

from clientserver import ClientServer


class Client(ClientServer):

    """Docstring for Server."""

    def __init__(self):
        super().__init__()

    def _init_tls(self):
        print("using client tls")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_cert_chain(
            expanduser("~/.mdb/cert.pem"), expanduser("~/.mdb/key.rsa")
        )
        context.load_verify_locations(expanduser("~/.mdb/cert.pem"))
        self.context = context

    def connect(self, hostname, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssl_sock = self.context.wrap_socket(sock, server_hostname=hostname)
        print(f"connecting to {hostname}:{port} ")
        ssl_sock.connect((hostname, port))
        print("connected")
        self.ssl_sock = ssl_sock

    def close(self):
        self.ssl_sock.close()


if __name__ == "__main__":
    opts = {"hostname": "localhost", "port": 2000}
    client = Client()

    message = {"gdb": "command to run", "list": list(range(22))}
    client.connect(**opts)
    client.send_message(message)
    message = client.recv_message()
    client.close()
