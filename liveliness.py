# Display the latest sensor samples from publisher
# 
# Ocean Technology Group
# SOEST, University of Hawaii
# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved, 2016
import os,time,zmq,json,sys
from datetime import datetime
sys.path.append(r'../node')
from helper import dt2ts,ts2dt
from twisted.internet.task import LoopingCall
from twisted.internet import reactor

#from tabulate import tabulate


context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect('tcp://localhost:9002')
socket.setsockopt_string(zmq.SUBSCRIBE,u'')


poller = zmq.Poller()
poller.register(socket,zmq.POLLIN)


D = {}

def taskRecv():
    socks = dict(poller.poll(500))
    if socket in socks and zmq.POLLIN == socks[socket]:
        msg = socket.recv_string()
        if len(msg):
            msg = msg.split(',',1)
            d = json.loads(msg[1])
            D[d['tag']] = d

def taskDisp():
    os.system('cls' if os.name == 'nt' else 'clear')
    for tag in sorted(D.keys()):
        #print(D[tag])
        print('- - - - -')
        print('{} ({} ago)'.format(tag,datetime.utcnow() - ts2dt(D[tag]['ts'])))
        for col in sorted(D[tag].keys()):
            print('\t{}={}'.format(col,D[tag][col]))

def taskLiveliness():
    global D
    for k in D.keys():
        if dt2ts(datetime.utcnow()) - D[k]['ts'] > 10*60:
            del D[k]

lcRecv = LoopingCall(taskRecv)
lcDisp = LoopingCall(taskDisp)
lcLiveliness = LoopingCall(taskLiveliness)
lcRecv.start(0.1)
lcDisp.start(1)
lcLiveliness.start(60)

reactor.run()

sys.exit()


'''while True:
    try:
        socks = dict(poller.poll(1000))
        if socket in socks and zmq.POLLIN == socks[socket]:
            msg = socket.recv_string()
            msg = msg.split(',',1)
            d = json.loads(msg[1])
            D[d['tag']] = d

            os.system('cls' if os.name == 'nt' else 'clear')
            for tag in sorted(D.keys()):
                #print(D[tag])
                print('- - - - -')
                print('{} ({:.1f}s ago)'.format(tag,dt2ts(datetime.utcnow()) - D[tag]['ts']))
                for col in D[tag].keys():
                    print('\t{}={}'.format(col,D[tag][col]))
            
    except KeyboardInterrupt:
        logger.info('User interrupted')
        break

socket.close()

'''
