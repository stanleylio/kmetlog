#!/bin/bash
# doesn't work in supervisor for some reason. not in use.
exit 0;
python zmq2stdout.py 127.0.0.1:9002 | python stdin2ws.py 9000