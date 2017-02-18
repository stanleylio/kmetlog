# store stuff from zmq to text file, with timestamps
# 
# SOEST, University of Hawaii
# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved, 2017
from __future__ import division
import zmq,logging,time,sys,traceback
sys.path.append('..')
import logging.handlers
from os import makedirs
from os.path import exists,join
from socket import gethostname
from importlib import import_module


config = import_module('config.{node}'.format(node=gethostname().replace('-','_')))


# product of this script, the raw text file
data_path = config.data_dir
if not exists(data_path):
    makedirs(data_path)

# log file for debugging use, may or may not include data depending on log level
log_path = config.log_dir
if not exists(log_path):
    makedirs(log_path)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
#fh = logging.FileHandler(join(log_path,'log2txt.log'))
fh = logging.handlers.RotatingFileHandler(join(log_path,'log2txt.log'),maxBytes=1e7,backupCount=5)
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logging.Formatter.converter = time.gmtime
formatter = logging.Formatter('%(asctime)s,%(name)s,%(levelname)s,%(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

topic = u''
context = zmq.Context()
socket = context.socket(zmq.SUB)
#socket.connect('tcp://localhost:9002')
#socket.connect('tcp://' + config.kmet1_ip + ':' + str(config.kmet1_port))
for feed in config.subscribeto:
    feed = 'tcp://' + feed
    logger.info('subscribing to ' + feed)
    socket.connect(feed)
socket.setsockopt_string(zmq.SUBSCRIBE,topic)
poller = zmq.Poller()
poller.register(socket,zmq.POLLIN)

f = open(join(data_path,'log2txt.txt'),'a',0)

logger.info('Logger is ready')

while True:
    try:
        socks = dict(poller.poll(1000))
        if socket in socks and zmq.POLLIN == socks[socket]:
            msg = socket.recv_string().strip()
            if len(msg):
                logger.debug(msg)
                f.write('{},{}\n'.format(time.time(),msg))
                f.flush()
    except KeyboardInterrupt:
        logger.info('User interrupted')
        break
    except:
        logger.warning(traceback.format_exc())

f.close()
socket.close()

logger.info('Logger terminated')
