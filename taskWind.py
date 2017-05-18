import sys,logging,time,traceback,pika,socket,json
from os.path import expanduser
sys.path.append(expanduser('~'))
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from node.config.config_support import import_node_config
from node.drivers.rmy85106 import RMY85106
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
        rmy = RMY85106(config.USWIND_PORT[0],config.USWIND_PORT[1])
        r = rmy.read()
        if r is None:
            return
        
        d = {'tag':'UltrasonicWind',
             'ts':time.time(),
             'UltrasonicWind_apparent_speed_mps':r['v'],
             'UltrasonicWind_apparent_direction_deg':r['d']}
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
LoopingCall(task).start(1)

logging.info(__file__ + ' is ready')
reactor.run()
logging.info(__file__ + ' terminated')
