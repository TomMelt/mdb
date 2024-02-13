import socket
import ssl
from os.path import expanduser

import pexpect  # type: ignore
from backend import GDBBackend
from client import Client
from clientserver import ClientServer
from utils import strip_bracketted_paste, strip_control_characters

N = 1


class Server(ClientServer):

    """Docstring for Server."""

    def __init__(self, opts):
        super().__init__()
        self.hostname = opts["hostname"]
        self.port = opts["port"]
        self.servers = []
        print(f"server started :: {self.hostname}:{self.port}")

    def _init_tls(self):
        print("using server tls")
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(
            expanduser("~/.mdb/cert.pem"), expanduser("~/.mdb/key.rsa")
        )
        self.context = context

    def start_server(self):
        pass


class DebugServer(Server):

    """Docstring for Server."""

    def __init__(self, opts):
        super().__init__(opts=opts)

        if opts["backend"].lower() == "gdb":
            backend = GDBBackend()
        else:
            msg = f"Backend [{backend}] is not implemented yet."
            raise NotImplementedError(msg)

        self.rank = opts["rank"]
        self.prompt = backend.prompt_string
        self.dbg_proc = None

    def handle_connection(self):
        message = self.recv_message()
        command = message["command"]
        print(f"running {command}")
        self.dbg_proc.sendline(command)
        self.dbg_proc.expect(self.prompt)
        result = self.dbg_proc.before.decode("utf-8")
        result = strip_bracketted_paste(result)
        result = strip_control_characters(result)
        message = {"result": result}
        self.send_message(message)

    def init_debug_proc(self):
        """
        initialize pexpect debug process
        """
        dbg_proc = pexpect.spawn("gdb -q", timeout=None)
        dbg_proc.expect(self.prompt)
        dbg_proc.sendline("set pagination off")
        dbg_proc.expect(self.prompt)
        dbg_proc.sendline("set confirm off")
        dbg_proc.expect(self.prompt)
        dbg_proc.sendline("start")
        dbg_proc.expect(self.prompt)
        self.dbg_proc = dbg_proc

    def notify_exchange(self, hostname, port):
        opts = {"hostname": hostname, "port": port}
        client = Client()
        client.connect(**opts)

        message = {"rank": 1, "hostname": self.hostname, "port": self.port}
        client.send_message(message)
        client.close()

    def start_server(self):
        bindsocket = socket.socket()
        bindsocket.bind((self.hostname, self.port))
        bindsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bindsocket.listen(5)

        while True:
            print(f"Listening on {self.hostname}:{self.port}")
            ssl_sock, fromaddr = bindsocket.accept()
            try:
                self.ssl_sock = self.context.wrap_socket(ssl_sock, server_side=True)
                self.handle_connection()
            except Exception as e:
                print(f"Error: {e}")
            finally:
                try:
                    self.ssl_sock.shutdown(socket.SHUT_RDWR)
                    self.ssl_sock.close()
                except:
                    continue


class ExchangeServer(Server):

    """Docstring for Server."""

    def __init__(self, opts):
        super().__init__(opts=opts)
        self.servers = []

    def handle_connection(self):
        message = self.recv_message()
        server = {
            "rank": message["rank"],
            "hostname": message["hostname"],
            "port": message["port"],
        }
        self.servers.append(server)

    def handle_command(self):
        command = self.recv_message()

        opts = {"hostname": self.hostname, "port": 2001}

        client = Client()
        client.connect(**opts)
        client.send_message(command)
        output = client.recv_message()

        self.send_message(output)

    def listen_for_debug_servers(self):
        bindsocket = socket.socket()
        bindsocket.bind((self.hostname, self.port))
        bindsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bindsocket.listen(5)

        while True:
            if len(self.servers) == N:
                break
            print(f"Listening on {self.hostname}:{self.port}")
            ssl_sock, fromaddr = bindsocket.accept()
            try:
                self.ssl_sock = self.context.wrap_socket(ssl_sock, server_side=True)
                self.handle_connection()
            except Exception as e:
                print(f"Error: {e}")
            finally:
                try:
                    self.ssl_sock.shutdown(socket.SHUT_RDWR)
                    self.ssl_sock.close()
                except:
                    continue

        print("ALL SEVERS CONNECTED")

    def listen_for_commands(self):
        bindsocket = socket.socket()
        bindsocket.bind((self.hostname, self.port))
        bindsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bindsocket.listen(5)

        while True:
            print("Listening for commands...")
            ssl_sock, fromaddr = bindsocket.accept()
            try:
                self.ssl_sock = self.context.wrap_socket(ssl_sock, server_side=True)
                self.handle_command()
            except Exception as e:
                print(f"Error: {e}")
            finally:
                try:
                    self.ssl_sock.shutdown(socket.SHUT_RDWR)
                    self.ssl_sock.close()
                except:
                    continue
