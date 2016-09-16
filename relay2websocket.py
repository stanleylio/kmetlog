import zmq,logging
from twisted.internet.task import LoopingCall
from twisted.internet import reactor

from autobahn.twisted.websocket import WebSocketServerFactory,\
     WebSocketServerProtocol,\
     listenWS


class BroadcastServerProtocol(WebSocketServerProtocol):
    def onOpen(self):
        self.factory.register(self)

    def onMessage(self, payload, isBinary):
        pass

    def connectionLost(self, reason):
        WebSocketServerProtocol.connectionLost(self, reason)
        self.factory.unregister(self)


class BroadcastServerFactory(WebSocketServerFactory):
    """
    Simple broadcast server broadcasting any message it receives to all
    currently connected clients.
    """

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
            print("registered client {}".format(client.peer))
            self.clients.append(client)

    def unregister(self, client):
        if client in self.clients:
            print("unregistered client {}".format(client.peer))
            self.clients.remove(client)

    def broadcast(self, msg):
        print("broadcasting message '{}' ..".format(msg))
        for c in self.clients:
            c.sendMessage(msg.encode('utf8'))
            print("message sent to {}".format(c.peer))


ServerFactory = BroadcastServerFactory
factory = ServerFactory(u'ws://localhost:9000')
factory.protocol = BroadcastServerProtocol
listenWS(factory)

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect('tcp://localhost:9002')
socket.setsockopt_string(zmq.SUBSCRIBE,u'kmet1_StarboardWind')


def task():
    s = socket.recv_string()
    print(s)
    factory.broadcast(s)

lc = LoopingCall(task)
lc.start(0.1)


reactor.run()

socket.close()


print('terminated')

