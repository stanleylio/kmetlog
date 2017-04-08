# store stuff from zmq to text file, with timestamps
# 
# Stanley H.I. Lio
# hlio@hawaii.edu
# University of Hawaii
# All Rights Reserved, 2017
import zmq,logging,time,sys,traceback
sys.path.append('..')
import logging.handlers
from os import makedirs
from os.path import exists,join
from socket import gethostname
from config.config_support import import_node_config


config = import_node_config()


# product of this script, the raw text file
# distinguished from (the now obsolete) log file, which is for debugging
data_path = config.data_dir
if not exists(data_path):
    makedirs(data_path)


#'DEBUG,INFO,WARNING,ERROR,CRITICAL'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.handlers.SysLogHandler(address='/dev/log')
logging.Formatter.converter = time.gmtime
#formatter = logging.Formatter('%(asctime)s,%(name)s,%(levelname)s,%(module)s.%(funcName)s,%(message)s')
formatter = logging.Formatter('%(name)s,%(levelname)s,%(module)s.%(funcName)s,%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

topic = u''
context = zmq.Context()
zsocket = context.socket(zmq.SUB)
for feed in config.subscribeto:
    feed = 'tcp://' + feed
    logger.info('subscribing to ' + feed)
    zsocket.connect(feed)
zsocket.setsockopt_string(zmq.SUBSCRIBE,topic)
poller = zmq.Poller()
poller.register(zsocket,zmq.POLLIN)

f = open(join(data_path,'log2txt.txt'),'a',0)

logger.info('log2txt is ready')
while True:
    try:
        socks = dict(poller.poll(1000))
        if zsocket in socks and zmq.POLLIN == socks[zsocket]:
            msg = zsocket.recv_string().strip()
            if len(msg):
                logger.info(msg)
                f.write('{},{}\n'.format(time.time(),msg))
                f.flush()
    except KeyboardInterrupt:
        logger.info('User interrupted')
        break
    except:
        logger.warning(traceback.format_exc())

f.close()
zsocket.close()
logger.info('Logger terminated')
