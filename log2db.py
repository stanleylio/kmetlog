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
from sqlalchemy import create_engine,Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import NoSuchTableError
from config import config
from socket import gethostname
#import db_configuration
import dbstuff
from os.path import expanduser


config = config[gethostname()]


#tags = [t['name'] for t in db_configuration.schema]
#print(tags)


#db_path = '/var/kmetlog/data'
#db_path = config['data_dir']
#if not exists(db_path):
#    makedirs(db_path)

#log_path = '/var/kmetlog/log'
log_path = config['log_dir']
if not exists(log_path):
    makedirs(log_path)

#db_file = join(db_path,'met.db')


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
    feed = 'tcp://' + feed + ':9002'
    logger.debug('subscribing to ' + feed)
    socket.connect(feed)

socket.setsockopt_string(zmq.SUBSCRIBE,protocol_tag)
poller = zmq.Poller()
poller.register(socket,zmq.POLLIN)

# database stuff
#engine = create_engine('sqlite:///' + db_file,echo=False)
dbname = 'kmetlog'
# the machine is behind firewall, on a network (to be) disconnected from the internet, hosting
# a MySQL database that only open to localhost, storing meteorological measurements soon to be
# made public... I don't think it needs a password at all.
engine = create_engine('mysql+mysqldb://root:' + open(expanduser('~/mysql_cred')).read() + '@localhost',
                       pool_recycle=3600,
                       echo=False)
engine.execute('CREATE DATABASE IF NOT EXISTS ' + dbname)
engine.execute('USE ' + dbname)
dbstuff.Base.metadata.create_all(engine)
meta = dbstuff.Base.metadata
#meta = MetaData()
#meta.bind = engine

Session = sessionmaker()
Session.configure(bind=engine)
session = Session()

tags = [table.name for table in meta.sorted_tables]
#print tags
#exit()

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
            except NoSuchTableError:
                logger.error('No such table: {}'.format(d['tag']))
            except:
                logger.error(traceback.format_exc())
    except KeyboardInterrupt:
        logger.info('User interrupted')
        break

socket.close()

logger.info('Logger terminated')
