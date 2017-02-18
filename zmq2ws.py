# redirect stuff from zmq to ws
#
# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved. 2017
import zmq,sys
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
sys.path.append('..')
from node.wsrelay import BroadcastServerProtocol,BroadcastServerFactory
from autobahn.twisted.websocket import WebSocketServerFactory,\
     WebSocketServerProtocol,\
     listenWS


if 3 != len(sys.argv):
    print('usage: python zmq2ws.py zmq_port ws_port')
    print('example: python zmq2ws.py 9002 9000')
    exit()

try:
    a,b = int(sys.argv[1]),int(sys.argv[2])
    zmq_port,ws_port = a,b
except:
    print('bad arguments: {}'.format(sys.argv[1:]))
    exit()

print('zmq: {} -> ws: {}'.format(zmq_port,ws_port))

topic = u''
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect('tcp://localhost:{}'.format(zmq_port))
socket.setsockopt_string(zmq.SUBSCRIBE,topic)
poller = zmq.Poller()
poller.register(socket,zmq.POLLIN)

ServerFactory = BroadcastServerFactory
factory = ServerFactory(u'ws://*:{}'.format(ws_port))
factory.protocol = BroadcastServerProtocol
listenWS(factory)


def taskListener():
    try:
        socks = dict(poller.poll(1000))
        if socket in socks and zmq.POLLIN == socks[socket]:
            m = socket.recv_string()
            print(m)
            factory.broadcast(m)
    except:
        traceback.print_exc()


LoopingCall(taskListener).start(0.01,now=False)
reactor.run()
socket.close()
