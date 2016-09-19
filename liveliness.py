# Display the latest sensor samples from publisher
# 
# Ocean Technology Group
# SOEST, University of Hawaii
# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved, 2016
import os,time,zmq,json,sys,traceback
from datetime import datetime
sys.path.append(r'../node')
from helper import dt2ts,ts2dt
from twisted.internet.task import LoopingCall
from twisted.internet import reactor

#from tabulate import tabulate


context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect('tcp://localhost:9002')
socket.setsockopt_string(zmq.SUBSCRIBE,u'kmet1_')

poller = zmq.Poller()
poller.register(socket,zmq.POLLIN)


D = {}  # latest samples of all received variables
Dt = {} # one list of timestamps per variable, max list length = 10
def taskRecv():
    try:
        socks = dict(poller.poll(100))
        if socket in socks and zmq.POLLIN == socks[socket]:
            msg = socket.recv_string()
            if len(msg):
                msg = msg.split(',',1)
                d = json.loads(msg[1])
                tag = d['tag']
                D[tag] = d
                
                if tag not in Dt:
                    Dt[tag] = []
                Dt[tag].append(d['ts'])
                while Dt[tag] is not None and len(Dt[tag]) > 10:
                    Dt[tag].pop(0)
    except Exception as e:
        traceback.print_exc()

def taskDisp():
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        os.system('du -sh /root/logging/data /root/logging/log')
        for tag in sorted(D.keys()):
            ago = dt2ts(datetime.utcnow()) - D[tag]['ts']
            s = '{}, {:.1f}s ago'.format(tag,ago)
            period = float('nan')
            if len(Dt[tag]) > 1:
                period = sum([p[0]-p[1] for p in zip(Dt[tag][1:],Dt[tag][0:-1])])/(len(Dt[tag]) - 1)
                s = s + ', {:.1f}s per sample'.format(period)
            # ago should be <= period.
            if ago > 2*period:
                s = s + ' (dead?)'
            print('')
            print(s)
            for col in sorted(D[tag].keys()):
                print('\t{}={}'.format(col,D[tag][col]))
    except:
        traceback.print_exc()

def taskLiveliness():
    global D
    for k in D.keys():
        if dt2ts(datetime.utcnow()) - D[k]['ts'] > 60*60:
            del D[k]


lcRecv = LoopingCall(taskRecv)
lcDisp = LoopingCall(taskDisp)
lcLiveliness = LoopingCall(taskLiveliness)
lcRecv.start(0.1)
lcDisp.start(1)
lcLiveliness.start(60)

reactor.run()


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

socket.close()'''
