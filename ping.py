import sys,socket
from os.path import expanduser
sys.path.append(expanduser('~'))
from node.send2server import post


m = socket.gethostname()
print(post(m,'http://grogdata.soest.hawaii.edu/api/4'))
