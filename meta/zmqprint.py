#
# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved. 2017
import zmq,sys,json,logging,traceback,math,time
import logging.handlers
from twisted.internet.task import LoopingCall
from twisted.internet import reactor


PERIOD = 1     # seconds


# ZMQ IPC stuff
topic = u'kmet1_'
context = zmq.Context()
zsocket = context.socket(zmq.SUB)
zsocket.connect('tcp://192.168.1.109:9002')
zsocket.setsockopt_string(zmq.SUBSCRIBE,topic)

poller = zmq.Poller()
poller.register(zsocket,zmq.POLLIN)



def taskSampler():
    try:
        socks = dict(poller.poll(10))
        if zsocket in socks and zmq.POLLIN == socks[zsocket]:
            #m = zsocket.recv()
            m = zsocket.recv_string()
            print(m)
    except:
        logger.warning(traceback.format_exc())

LoopingCall(taskSampler).start(0.1)
reactor.run()
zsocket.close()
