import sys,logging,time,traceback,pika,socket,json,argparse
from os.path import expanduser
sys.path.append(expanduser('~'))
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from node.config.config_support import import_node_config
from cred import cred


exchange = 'uhcm'
config = import_node_config()
nodeid = socket.gethostname()

parser = argparse.ArgumentParser(description='')
parser.add_argument('daq',metavar='daq',type=str,
                    help='One of {hv,lv}')
args = parser.parse_args()

assert args.daq in ['hv','lv','fc']


def daq_init():
    logging.debug('Initializing DAQ')
    if 'hv' == args.daq:
        from node.drivers.adam4017 import ADAM4017
        daq = ADAM4017('{:02d}'.format(config.DAQ_HV_PORT[1]),
                       config.DAQ_HV_PORT[0],
                       config.DAQ_HV_PORT[2])
        if not daq.CheckModuleName():
            logging.critical('Cannot reach the DAQ')
            return None
        if not any([daq.SetInputRange(5) for tmp in range(3)]):   # any() is short-circuited
            logging.critical('Unable to set DAQ input range')
            return None
        return daq
    elif 'lv' == args.daq:
        from node.drivers.adam4018 import ADAM4018
        daq = ADAM4018('{:02d}'.format(config.DAQ_LV_PORT[1]),
                       config.DAQ_LV_PORT[0],
                       config.DAQ_LV_PORT[2])
        if not daq.CheckModuleName():
            logging.critical('Cannot reach the DAQ')
            return None
        if not any([daq.SetInputRange(50e-3) for tmp in range(3)]):
            logging.critical('Unable to set DAQ input range')
            return None
        return daq
    elif 'fc' == args.daq:
        from node.drivers.adam4080 import ADAM4080
        daq = ADAM4080('{:02d}'.format(config.DAQ_F_PORT[1]),
                       config.DAQ_F_PORT[0],
                       config.DAQ_F_PORT[2])
        if not daq.CheckModuleName():
            logging.critical('Cannot reach the DAQ')
            return
        return daq


logging.info('Checking DAQ: ID{:02d} on {} at {}...'.format(config.DAQ_HV_PORT[1],config.DAQ_HV_PORT[0],config.DAQ_HV_PORT[2]))
#logging.info('PASS' if daq_init() is not None else 'FAIL')
#exit


def rabbit_init():
    credentials = pika.PlainCredentials('nuc',cred['rabbitmq'])
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost',5672,'/',credentials))
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange,type='topic',durable=True)
    return connection,channel

def task():
    global daq,connection,channel

    try:
        if daq is None:
            daq = daq_init()

        r = daq.ReadAll()
        if r is None:
            logging.error('Unable to read DAQ')
            daq = None
            return

        d = {'tag':args.daq,
             'ts':time.time(),
             'r':r}
        m = json.dumps(d,separators=(',',':'))

        print(m)
        channel.basic_publish(exchange=exchange,
                              routing_key=args.daq + '.m',
                              body=m,
                              properties=pika.BasicProperties(delivery_mode=1,  # non-persistent
                                                              content_type='text/plain',
                                                              expiration=str(5*1000),
                                                              timestamp=time.time()))
    except pika.exceptions.ConnectionClosed:
        connection,channel = None,None
        logging.error('connection closed')  # connection to the local exchange closed
    except:
        traceback.print_exc()


connection,channel = rabbit_init()
daq = daq_init()
LoopingCall(task).start(1)

logging.info(__file__ + ' is ready')
reactor.run()
del daq
logging.info(__file__ + ' terminated')
