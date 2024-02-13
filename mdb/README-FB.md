# instructions to run:

Easiest to use tmux - you will need three terminal panes open

You will also need to configure the tls cert/key which I have hardcoded (currently to ~/.mdb)

```bash
mkdir -p ~/.mdb
cd ~/.mdb
openssl req -x509 -newkey rsa:4096 -keyout key.rsa -out cert.pem -sha256 -days 365 -nodes -subj "/C=XX/ST=mdb/L=mdb/O=mdb/OU=mdb/CN=localhost"
```

Now you can try running the server (which is very manual atm)

I run the commands from the same directory as the `exchange_server.py` file

1. in the 1st window/pane run `python exchange_server.py`
2. in the 2nd window/pane run `python debug_server.py`
3. finally in the 3rd pane run `python client.py` (you can keep re-running this command as many times as you like)

The final command should output the gdb version. I get the following output:

## PANE 1

```
$ python exchange_server.py
using server tls
server started :: localhost:2000
Listening on localhost:2000
ALL SEVERS CONNECTED
Listening for commands...
using client tls
connecting to localhost:2001
connected
Listening for commands...
```

## PANE 2

```
$ python debug_server.py
using server tls
server started :: localhost:2001
using client tls
connecting to localhost:2000
connected
Listening on localhost:2001
running show version
Listening on localhost:2001
```

## PANE 3

```
$ python client.py
using client tls
connecting to localhost:2000
connected
 show version
GNU gdb (Ubuntu 12.1-0ubuntu1~22.04) 12.1
Copyright (C) 2022 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
Type "show copying" and "show warranty" for details.
This GDB was configured as "x86_64-linux-gnu".
Type "show configuration" for configuration details.
For bug reporting instructions, please see:
<https://www.gnu.org/software/gdb/bugs/>.
Find the GDB manual and other documentation resources online at:
    <http://www.gnu.org/software/gdb/documentation/>.

For help, type "help".
Type "apropos word" to search for commands related to "word".
```
