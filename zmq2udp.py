# relay met data to siscon
# handles data collection, formatting and UDP broadcast
# to be run on kmet-bbb up on the met. mast
#
# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved. 2016
import zmq,sys,json,logging,traceback,math,time,socket
import logging.handlers
from twisted.internet.task import LoopingCall
from twisted.internet import reactor



UDP_PORT = 9007


# Logging
'''DEBUG,INFO,WARNING,ERROR,CRITICAL'''
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # "global"?
fh = logging.handlers.RotatingFileHandler('/var/kmetlog/log/zmq2udp.log',maxBytes=1e7,backupCount=5)
fh.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logging.Formatter.converter = time.gmtime
formatter = logging.Formatter('%(asctime)s,%(name)s,%(levelname)s,%(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


# ZMQ IPC stuff
topic = u'kmet1_'
context = zmq.Context()
zsocket = context.socket(zmq.SUB)
zsocket.connect('tcp://127.0.0.1:9002')
zsocket.setsockopt_string(zmq.SUBSCRIBE,topic)

poller = zmq.Poller()
poller.register(zsocket,zmq.POLLIN)


# communication
sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.bind(('', 0))
sock.setsockopt(SOL_SOCKET,SO_BROADCAST,1)


def send(s):
    try:
        logger.debug(s)
        sock.sendto(s,('<broadcast>',UDP_PORT))
    except:
        logger.error(traceback.format_exc())


D = {}  # latest samples of all received variables


def taskSampler():
    try:
        socks = dict(poller.poll(500))
        if zsocket in socks and zmq.POLLIN == socks[zsocket]:
            #m = zsocket.recv()
            m = socket.recv_string()
            logger.debug(m)
            m = m.split(',',1)

            d = json.loads(m[1])
            if d['tag'] not in tags:
                continue

            D[d['tag']] = d
    except TypeError:
        logger.warning(traceback.format_exc())
        logger.warning(msg)
    except KeyboardInterrupt:
        logger.info('User interrupted')
        break
    except:
        logger.warning(traceback.format_exc())

def taskBroadcast():
    s = '{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n'.format(
        0,  # Panel temperature (now obsolete)
        D['RMYRTD']['T'],       # RTD (Deg.C)
        D['Rotronics']['RH'],   # Humidity (%)
        D.get('Rotronics',{}).get('T',0),                   # Humidity_temperature
        D.get('BucketRain',{}).get('accumulation_mm',0),    # Bucket_rain_gauge
        PSP (mV)
        PIR (mV)
        PIR Case thermistor (V)
        PIR Dome thermistor (V)
        RTD fan speed
        Humidity fan speed
        PAR (V)
        Relative wind speed (ultrasonic, knot)
        Relative wind direction
        Weather condition (optical)
        Precipitation (optical, mm)
        Precipitation accumulation (optical)
        )
    send(s)

LoopingCall(taskSampler).start(0.5)
LoopingCall(taskBroadcast).start(60)

reactor.run()

zsocket.close()
