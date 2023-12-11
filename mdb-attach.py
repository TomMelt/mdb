import subprocess as sub
import pexpect
import threading
import os
import signal
import sys
import pty

dbg_procs = []

def main():

    connect()

def connect_proc(port):
    c = pexpect.spawn(f'gdb -q -ex \"target remote localhost:{port}\" ./a.out', timeout=None)
    c.sendline('b MAIN__')
    c.sendline('c')
    # c = sub.Popen(['gdb', '-ex', f'\"target remote localhost:{port}\"', './a.out'])
    return c

def close_procs(sig, frame):

    # for proc in dbg_procs:
    #     proc.close()

    sys.exit(0)

def connect():

    dbg_threads = []

    for i in range(2):
        port = 2000+i
        c = connect_proc(port)
        dbg_procs.append(c)

    signal.signal(signal.SIGINT, close_procs)

    while True:
        sys.stdout.write("\r")
        rank = int(input('rank to debug: '))
        c = dbg_procs[rank]
        # file = open(f'log.{port}', 'wb')
        # c.logfile_read = file
        c.interact()

if __name__ == "__main__":
    main()
