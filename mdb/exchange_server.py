from server import ExchangeServer

opts = {"hostname": "localhost", "port": 2000}
server = ExchangeServer(opts=opts)
server.listen_for_debug_servers()
server.listen_for_commands()
