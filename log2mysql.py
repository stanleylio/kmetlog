# is anyone even using this?
# used on kmet-rpi1, preping for kmet-bbb3
# WORK IN PROGRESS
#
# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved. 2017
import zmq,sys,json,logging,traceback,time,random
import logging.handlers
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from os.path import exists,join,expanduser
from socket import gethostname
sys.path.append('..')
from node.parse_support import pretty_print
from node.storage.storage2 import storage
from config.config_support import import_node_config


config = import_node_config()


#'DEBUG,INFO,WARNING,ERROR,CRITICAL'
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
handler = logging.handlers.SysLogHandler(address='/dev/log')
logging.Formatter.converter = time.gmtime
formatter = logging.Formatter('%(asctime)s,%(name)s,%(levelname)s,%(module)s.%(funcName)s,%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# ZMQ IPC stuff
topic = u'kmet1'
context = zmq.Context()
zsocket = context.socket(zmq.SUB)
for feed in config.subscribeto:
    feed = 'tcp://' + feed
    logger.info('subscribing to ' + feed)
    zsocket.connect(feed)
zsocket.setsockopt_string(zmq.SUBSCRIBE,topic)
poller = zmq.Poller()
poller.register(zsocket,zmq.POLLIN)


store = storage(user='root',passwd=open(expanduser('~/mysql_cred')).read().strip(),dbname='kmetlog')


def taskSampler():
    try:
        socks = dict(poller.poll(100))
        if zsocket in socks and zmq.POLLIN == socks[zsocket]:
            print('= = = = =')
            #m = zsocket.recv()
            m = zsocket.recv_string()
            logger.debug(m)
            
# - - - - -
# slow machine?
# - - - - -
#            if random.random() >= 0.1:
#                return
# - - - - -
            
            m = m.split(',',1)  # ignore the "kmet1," part
            d = json.loads(m[1])
            table = d['tag']
            tmp = {k:d[k] for k in set(store.get_list_of_columns(table))}
            store.insert(table,tmp)
            pretty_print(tmp)
    except:
        logger.exception(traceback.format_exc())
        logger.exception(m)

LoopingCall(taskSampler).start(0.001)
reactor.run()
zsocket.close()
