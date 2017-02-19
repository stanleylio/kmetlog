# STDIN -> ws
#
# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved. 2017
import zmq,sys,logging,traceback
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
sys.path.append('..')
from node.wsrelay import BroadcastServerProtocol,BroadcastServerFactory
from autobahn.twisted.websocket import WebSocketServerFactory,\
     WebSocketServerProtocol,\
     listenWS


if 2 != len(sys.argv):
    logging.info('usage: python stdin2ws.py ws_port')
    logging.info('example: python stdin2ws.py 9000')
    exit()

try:
    ws_port = sys.argv[1]
except:
    ('bad arguments: {}'.format(sys.argv[1:]))
    exit()

logging.info('ws: {}'.format(ws_port))

ServerFactory = BroadcastServerFactory
factory = ServerFactory(u'ws://*:' + ws_port)
factory.protocol = BroadcastServerProtocol
listenWS(factory)


def taskListener():
    try:
        m = sys.stdin.readline().strip()
        logging.debug(m)
        factory.broadcast(m)
    except:
        traceback.print_exc()


LoopingCall(taskListener).start(0.01,now=False)
reactor.run()
