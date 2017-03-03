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
sys.path.append('..')
from node.parse_support import pretty_print
from node.storage.storage2 import storage
from os.path import exists,join,expanduser
from socket import gethostname
from importlib import import_module


config = import_module('config.{node}'.format(node=gethostname().replace('-','_')))


# Logging
log_path = config.log_dir
if not exists(log_path):
    makedirs(log_path)

'''DEBUG,INFO,WARNING,ERROR,CRITICAL'''
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # "global"?
fh = logging.handlers.RotatingFileHandler(join(log_path,'log2db.log'),maxBytes=1e7,backupCount=5)
fh.setLevel(logging.DEBUG)
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
for feed in config.subscribeto:
    feed = 'tcp://' + feed
    logger.info('subscribing to ' + feed)
    zsocket.connect(feed)
#zsocket.connect('tcp://127.0.0.1:9002')
#zsocket.connect('tcp://192.168.1.109:9002')
zsocket.setsockopt_string(zmq.SUBSCRIBE,topic)
poller = zmq.Poller()
poller.register(zsocket,zmq.POLLIN)


store = storage(user='root',passwd=open(expanduser('~/mysql_cred')).read().strip(),dbname='kmetlog')


# mapping new tags to old tags. temporary hack for the demo. won't be needing this on the new logger.
tagmap = {'ts':'ts',
          'PAR_V':'par_V',
          'PIR_mV':'ir_mV',
          'PIR_case_V':'t_case_V',
          'PIR_dome_V':'t_dome_V',
          'PSP_mV':'psp_mV',
          'UltrasonicWind_apparent_speed_mps':'apparent_speed_mps',
          'UltrasonicWind_apparent_direction_deg':'apparent_direction_deg',
          'OpticalRain_weather_condition':'weather_condition',
          'OpticalRain_instantaneous_mmphr':'instantaneous_mmphr',
          'OpticalRain_accumulation_mm':'accumulation_mm',
          'BucketRain_accumulation_mm':'accumulation_mm',
          'Rotronics_T_C':'T',
          'Rotronics_RH_percent':'RH',
          'RMYRTD_T_C':'T',
          'BME280_T_C':'T',
          'BME280_P_kPa':'P',
          'BME280_RH_percent':'RH',
          'RMYRTD_Fan_rpm':'RadFan2_rpm',
          'Rotronics_Fan_rpm':'RadFan1_rpm',
          }

def taskSampler():
    try:
        socks = dict(poller.poll(1000))
        if zsocket in socks and zmq.POLLIN == socks[zsocket]:
            #m = zsocket.recv()
            m = zsocket.recv_string()
            logger.debug(m)

# - - - - -
# slow machine?
# - - - - -
#            if random.random() >= 0.08:
#                return
# - - - - -
            
            m = m.split(',',1)  # ignore the "kmet1_BLAH," part
            d = json.loads(m[1])

            table = d['tag']
            tmp = {k:d[tagmap[k]] for k in set(store.get_list_of_columns(table))}
            store.insert(table,tmp)
            pretty_print(tmp)
    except TypeError:
        logger.error(traceback.format_exc())
        logger.error(msg)
    except:
        logger.error(traceback.format_exc())


LoopingCall(taskSampler).start(0.001)

reactor.run()
zsocket.close()
