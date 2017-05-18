import sys,logging,time,traceback,pika,socket,json
from os.path import expanduser
sys.path.append(expanduser('~'))
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from node.config.config_support import import_node_config
from node.drivers.org815dr import ORG815DR
from cred import cred


exchange = 'uhcm'
config = import_node_config()
nodeid = socket.gethostname()


def rabbit_init():
    credentials = pika.PlainCredentials('nuc',cred['rabbitmq'])
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost',5672,'/',credentials))
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange,type='topic',durable=True)
    return connection,channel

def task():
    global connection,channel

    try:
        org = ORG815DR(config.OPTICALRAIN_PORT[0],config.OPTICALRAIN_PORT[1])
        r = org.read()
        org.reset_accumulation_if_required()
        if r is None:
            return
        r['ts'] = time.time()
        r['tag'] = 'OpticalRain'
        m = json.dumps(r,separators=(',',':'))
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
LoopingCall(task).start(1)

logging.info(__file__ + ' is ready')
reactor.run()
logging.info(__file__ + ' terminated')
