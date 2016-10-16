#
# 
# Stanley H.I. Lio
# hlio@hawaii.edu
# Ocean Technology Group
# SOEST, University of Hawaii
# All Rights Reserved, 2016
import sys,zmq,logging,json,time,traceback,serial
import logging.handlers
sys.path.append(r'../node')
from datetime import datetime
from os import makedirs
from os.path import exists,join
import config


log_path = '/var/logging/log'
if not exists(log_path):
    makedirs(log_path)

#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.handlers.RotatingFileHandler(join(log_path,'read_wind.log'),
                                          maxBytes=1e7,
                                          backupCount=5)
fh.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logging.Formatter.converter = time.gmtime
formatter = logging.Formatter('%(asctime)s,%(name)s,%(levelname)s,%(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


logger.debug('binding 0MQ port...')
#zmq_port = 'tcp://*:9002'
zmq_port = 'tcp://*:' + str(config.kmet1_port)
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind(zmq_port)
logger.info('Broadcasting at {}'.format(zmq_port))


last_transmitted = datetime.utcnow()
def send(d):
    try:
        if 'tag' in d:
            topic = d['tag']
            s = json.dumps(d,separators=(',',':'))
            s = 'kmet1_{topic},{msg}'.format(msg=s,topic=topic)
            logger.debug(s)
        else:
            s = ''
        global last_transmitted
        last_transmitted = datetime.utcnow()
        socket.send_string(s)
    except:
        logger.error(traceback.format_exc())


def parseRMY(line):
    line = line.strip().split(',')
    if line[0] == '$WIMWV':
        tmp = line[5].split(' ')
        return {'port':{'apparent_direction_deg':float(line[1]),'apparent_speed_mps':float(line[3])*0.514444},
                'starboard':{'apparent_direction_deg':float(tmp[1]),'apparent_speed_mps':float(tmp[2])*0.514444}}


with serial.Serial('/dev/ttyUSB0',4800,timeout=1) as s:
    while True:
        try:
            line = s.readline()
            if len(line):
                r = parseRMY(line)
                if r is not None:
                    ts = datetime.utcnow()
                    d = {'tag':'PortWind',
                         'ts':ts,
                         'apparent_direction_deg':r['port']['apparent_direction_deg'],
                         'apparent_speed_mps':r['port']['apparent_speed_mps']}
                    send(d)
                    d = {'tag':'StarboardWind',
                         'ts':ts,
                         'apparent_direction_deg':r['starboard']['apparent_direction_deg'],
                         'apparent_speed_mps':r['starboard']['apparent_speed_mps']}
                    send(d)
        except KeyboardInterrupt:
            logging.info('user interrupted')
            break
        except:
            logger.error(traceback.format_exc())

logging.info('Terminated')
