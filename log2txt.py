# Subscribe to sensor feed and write everything received to text file
# 
# Ocean Technology Group
# SOEST, University of Hawaii
# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved, 2016
import zmq,logging,time,sys
import logging.handlers
from os import makedirs
from os.path import exists,join
from datetime import datetime
sys.path.append('../node')
from helper import dt2ts


# product of this script, the raw text file
data_path = 'data'
if not exists(data_path):
    makedirs(data_path)

# log file for debugging use, may or may not include data depending on log level
log_path = 'log'
if not exists(log_path):
    makedirs(log_path)

logger = logging.getLogger(__name__)
#logger = logging.getLogger('met_log_raw')
logger.setLevel(logging.INFO)
#fh = logging.FileHandler(join(log_path,'log2txt.log'))
fh = logging.handlers.RotatingFileHandler(join(log_path,'log2txt.log'),
                                          maxBytes=1e8,
                                          backupCount=5)
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logging.Formatter.converter = time.gmtime
formatter = logging.Formatter('%(asctime)s,%(name)s,%(levelname)s,%(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect('tcp://localhost:9002')

# get everything
socket.setsockopt_string(zmq.SUBSCRIBE,u'')
# get only selected topic
#socket.setsockopt_string(zmq.SUBSCRIBE,u'kmet1_PSP,')

poller = zmq.Poller()
poller.register(socket,zmq.POLLIN)

f = open(join(data_path,'log2txt.txt'),'a',1)

logger.info('Logger is ready')

while True:
    try:
        socks = dict(poller.poll(1000))
        if socket in socks and zmq.POLLIN == socks[socket]:
            msg = socket.recv_string()
            if len(msg):
                logger.debug(msg)
                dt = datetime.utcnow()
                ts = dt2ts(dt)
                #f.write('{},{},{}\n'.format(dt,ts,msg))
                f.write('{},{}\n'.format(ts,msg))
                f.flush()
    except KeyboardInterrupt:
        logger.info('User interrupted')
        break
    except Exception as e:
        logger.warning(e)

f.close()
socket.close()

logger.info('Logger terminated')
