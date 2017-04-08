# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved. 2017
import zmq,sys,json,logging,traceback,time,random,MySQLdb
import logging.handlers
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from os.path import exists,join,expanduser
from socket import gethostname
sys.path.append('..')
from node.parse_support import pretty_print
from node.storage.storage2 import storage
from config.config_support import import_node_config
from service_discovery import get_publisher_list


config = import_node_config()


#'DEBUG,INFO,WARNING,ERROR,CRITICAL'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.handlers.SysLogHandler(address='/dev/log')
logging.Formatter.converter = time.gmtime
formatter = logging.Formatter('%(asctime)s,%(name)s,%(levelname)s,%(module)s.%(funcName)s,%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# ZMQ IPC stuff
topic = u'kmet1'
context = zmq.Context()
zsocket = context.socket(zmq.SUB)


a = set(config.subscribeto)         # feeds found in config
b = set(get_publisher_list(topic))  # feeds found in the network
feeds = a.union(b)
for feed in feeds:
    feed = 'tcp://' + feed
    logger.info('subscribing to ' + feed)
    zsocket.connect(feed)
zsocket.setsockopt_string(zmq.SUBSCRIBE,topic)
poller = zmq.Poller()
poller.register(zsocket,zmq.POLLIN)

def init_storage():
    from cred import cred
    #return storage(user='root',passwd=open(expanduser('~/mysql_cred')).read().strip(),dbname='kmetlog')
    return storage(user='root',passwd=cred['mysql'],dbname='kmetlog')
store = init_storage()

def taskSampler():
    global store
    try:
        socks = dict(poller.poll(1000))
        if zsocket in socks and zmq.POLLIN == socks[zsocket]:
            print('= = = = = = = = = =')
            m = zsocket.recv()
            #m = zsocket.recv_string()
            logger.debug(m)
# - - - - -
# slow machine?
# - - - - -
#            if random.random() >= 0.1:
#                return
# - - - - -
            tmp = m.split(',',1)  # ignore the "kmet1," part
            d = json.loads(tmp[1])
            table = d['tag']
            tmp = {k:d[k] for k in store.get_list_of_columns(table)}
            store.insert(table,tmp)
            pretty_print(tmp)
    except MySQLdb.OperationalError,e:
        if e.args[0] in (MySQLdb.constants.CR.SERVER_GONE_ERROR,MySQLdb.constants.CR.SERVER_LOST):
            store = init_storage()
    except:
        logger.exception(traceback.format_exc())
        logger.exception(m)

logger.info('log2mysql is ready')
LoopingCall(taskSampler).start(0.001)
reactor.run()
zsocket.close()
