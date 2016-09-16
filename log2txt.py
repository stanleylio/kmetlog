# Subscribe to sensor feed and write everything received to text file
# 
# Ocean Technology Group
# SOEST, University of Hawaii
# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved, 2016
import zmq,logging,time
import logging.handlers
from os import makedirs
from os.path import exists,join


log_path = 'log'
if not exists(log_path):
    makedirs(log_path)

logger = logging.getLogger(__name__)
#logger = logging.getLogger('met_log_raw')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(join(log_path,'kmet_raw.txt'))
#fh = logging.handlers.RotatingFileHandler(join(log_path,'kmet_raw.txt'),
#                                          maxBytes=1e8,
#                                          backupCount=10)
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

logger.info('Logger is ready')

while True:
    try:
        socks = dict(poller.poll(1000))
        if socket in socks and zmq.POLLIN == socks[socket]:
            msg = socket.recv_string()
            logger.debug(msg)
    except KeyboardInterrupt:
        logger.info('User interrupted')
        break

socket.close()

logger.info('Logger terminated')
