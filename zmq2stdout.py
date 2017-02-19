# 0MQ -> STDOUT, one line per message
# Example: python zmqprint.py 127.0.0.1:9002 192.168.1.109:9002 --topic kmet1_
#
# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved. 2017
import zmq,sys,json,logging,traceback,math,time,argparse
import logging.handlers
from twisted.internet.task import LoopingCall
from twisted.internet import reactor


parser = argparse.ArgumentParser(description="""Redirect zmq to STDOUT. Example: python zmq2stdout.py 127.0.0.1:9002 --topic kmet1_""")
parser.add_argument('zmq_sockets',type=str,nargs='+')
parser.add_argument('--topic',dest='zmq_topic',default=u'',type=unicode)
args = parser.parse_args()


context = zmq.Context()
zsocket = context.socket(zmq.SUB)
logging.info('subscribe to')
for sock in args.zmq_sockets:
    zsocket.connect('tcp://' + sock)
    logging.info(sock)
logging.info('topic = {}'.format(args.zmq_topic))
zsocket.setsockopt_string(zmq.SUBSCRIBE,args.zmq_topic)
poller = zmq.Poller()
poller.register(zsocket,zmq.POLLIN)


def taskSampler():
    try:
        socks = dict(poller.poll(1000))
        if zsocket in socks and zmq.POLLIN == socks[zsocket]:
            #m = zsocket.recv()
            m = zsocket.recv_string()
            sys.stdout.write(m + '\n')  # ?
            sys.stdout.flush()
    except:
        logging.error(traceback.format_exc())


LoopingCall(taskSampler).start(0.001)
reactor.run()
zsocket.close()
