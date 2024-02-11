from server import DebugServer

opts = {"hostname": "localhost", "port": 2001}
server = DebugServer(opts=opts)
server.notify_exchange(hostname="localhost", port=2000)
server.start_server()
