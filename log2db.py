# Subscribe to sensor feed and store data to sqlite3 database
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
import json,traceback
from sqlalchemy import create_engine,Table,MetaData
#from sqlalchemy.orm import sessionmaker
import db_configuration
from config import config
from socket import gethostname


config = config[gethostname()]


tags = [t['name'] for t in db_configuration.schema]
print(tags)


#db_path = '/var/logging/data'
db_path = config['data_dir']
if not exists(db_path):
    makedirs(db_path)

#log_path = '/var/logging/log'
log_path = config['log_dir']
if not exists(log_path):
    makedirs(log_path)

db_file = join(db_path,'met.db')


#logging.basicConfig()

logger = logging.getLogger(__name__)
#logger = logging.getLogger('met_log_db')
logger.setLevel(logging.DEBUG)
#fh = logging.FileHandler(join(log_path,'kmet_db.log'))
fh = logging.handlers.RotatingFileHandler(join(log_path,'log2db.log'),
                                          maxBytes=1e7,
                                          backupCount=5)
fh.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
logging.Formatter.converter = time.gmtime
formatter = logging.Formatter('%(asctime)s,%(name)s,%(levelname)s,%(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


protocol_tag = u'kmet1_'
context = zmq.Context()
socket = context.socket(zmq.SUB)


# localhost, 192.168.1.109 (kmet-bbb), 192.168.1.167 (kmet-bbb-wind)...
#socket.connect('tcp://localhost:9002')
#socket.connect('tcp://localhost:' + str(config.kmet1_port))
#socket.connect('tcp://' + config.kmet1_ip + ':9002')
#socket.connect('tcp://192.168.1.109:9002')
#socket.connect('tcp://192.168.1.167:9002')

for feed in config['subscribeto']:
    socket.connect('tcp://' + feed + ':9002')


socket.setsockopt_string(zmq.SUBSCRIBE,protocol_tag)
poller = zmq.Poller()
poller.register(socket,zmq.POLLIN)

# database stuff
engine = create_engine('sqlite:///' + db_file,echo=False)
meta = MetaData()
meta.bind = engine

logger.info('Logger is ready')


while True:
    try:
        socks = dict(poller.poll(1000))
        if socket in socks and zmq.POLLIN == socks[socket]:
            msg = socket.recv_string()
            logger.debug(msg)
            msg = msg.split(',',1)
            try:
                d = json.loads(msg[1])
                if d['tag'] in tags:
                    #print(d)

                    m = Table(d['tag'],meta,autoload=True,autoload_with=engine)
                    engine.execute(m.insert(),**d)
                    
                    #session.add(d)
                    #session.commit()
                else:
                    logger.debug('unknown message: {},{}'.format(msg[0],msg[1]))
            except ValueError:
                logger.warning(traceback.format_exc())
    except KeyboardInterrupt:
        logger.info('User interrupted')
        break

socket.close()

logger.info('Logger terminated')
