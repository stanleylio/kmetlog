import zmq,logging,time
import logging.handlers
from os import makedirs
from os.path import exists,join
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketServerFactory,\
     WebSocketServerProtocol,\
     listenWS


log_path = 'log'
if not exists(log_path):
    makedirs(log_path)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
fh = logging.handlers.RotatingFileHandler(join(log_path,'zmq2ws.log'),
                                          maxBytes=1e7,
                                          backupCount=3)
fh.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logging.Formatter.converter = time.gmtime
formatter = logging.Formatter('%(asctime)s,%(name)s,%(levelname)s,%(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


class BroadcastServerProtocol(WebSocketServerProtocol):
    def onOpen(self):
        self.factory.register(self)

    def onMessage(self, payload, isBinary):
        pass

    def connectionLost(self, reason):
        WebSocketServerProtocol.connectionLost(self, reason)
        self.factory.unregister(self)


class BroadcastServerFactory(WebSocketServerFactory):
    def __init__(self, url):
        WebSocketServerFactory.__init__(self, url)
        self.clients = []
        self.v = 50
        self.tick()

    def tick(self):
        pass
        #self.broadcast('haha!')
        #reactor.callLater(0.1, self.tick)
        #reactor.stop()

    def register(self, client):
        if client not in self.clients:
            logger.info("registered client {}".format(client.peer))
            self.clients.append(client)

    def unregister(self, client):
        if client in self.clients:
            logger.info("unregistered client {}".format(client.peer))
            self.clients.remove(client)

    def broadcast(self, msg):
        #logger.info("broadcasting message '{}'".format(msg))
        for c in self.clients:
            c.sendMessage(msg.encode('utf8'))
            logger.debug("message sent to {}".format(c.peer))


# relay this...
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect('tcp://localhost:9002')
socket.setsockopt_string(zmq.SUBSCRIBE,u'')

# ... to this
ServerFactory = BroadcastServerFactory
factory = ServerFactory(u'ws://*:9000')
factory.protocol = BroadcastServerProtocol
listenWS(factory)


poller = zmq.Poller()
poller.register(socket,zmq.POLLIN)
def task():
    socks = dict(poller.poll(1000))
    if socket in socks and zmq.POLLIN == socks[socket]:
        s = socket.recv_string()
        logger.debug(s)
        factory.broadcast(s)

lc = LoopingCall(task)
lc.start(0.1)

reactor.run()

socket.close()

logger.info('terminated')
