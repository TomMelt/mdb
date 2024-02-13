from server import DebugServer

opts = {"hostname": "localhost", "port": 2001, "rank": 1, "backend": "gdb"}
server = DebugServer(opts=opts)
server.notify_exchange(hostname="localhost", port=2000)
server.init_debug_proc()
server.start_server()
