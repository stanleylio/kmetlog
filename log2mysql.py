# Don't know where consumers are or how many there are, so can't do Shovel;
# Consumers subscribe to bbb xchange -> it will need to handle network failure.
#
# Stanley H.I. Lio
# hlio@hawaii.edu
# University of Hawaii
# All Rights Reserved. 2017
import sys,json,traceback,time,math,pika,MySQLdb,logging
from os.path import expanduser,basename
sys.path.append(expanduser('~'))
from datetime import datetime
from node.storage.storage2 import storage
from node.parse_support import parse_message,pretty_print
from cred import cred


logging.basicConfig(level=logging.DEBUG)


exchange = 'uhcm'
table = 'kmetlog'       # unforseen consequence...
queue_name = basename(__file__)


def init_storage():
    return storage(user='root',passwd=cred['mysql'],dbname='kmetlog')
store = init_storage()


def rabbit_init():
    credentials = pika.PlainCredentials('nuc',cred['rabbitmq'])
    connection = pika.BlockingConnection(pika.ConnectionParameters('166.122.96.98',5672,'/',credentials))
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange,type='topic',durable=True)
    result = channel.queue_declare(queue=queue_name,
                                   durable=False,
                                   exclusive=True,
                                   auto_delete=True,
                                   arguments={'x-message-ttl':10*1000})
    channel.basic_qos(prefetch_count=1)
    channel.queue_bind(exchange=exchange,
                       queue=queue_name,
                       routing_key='samples')
    return connection,channel
connection,channel = None,None


def callback(ch,method,properties,body):
    global store
    try:
        d = json.loads(body)
        d['ReceptionTime'] = time.time()
        d = {k:d[k] for k in store.get_list_of_columns(table) if k in d}
        store.insert(table,d)
        print('= = = = = = = = = = = = = = =')
        pretty_print(d)
    except MySQLdb.OperationalError:
        traceback.print_exc()
        store = init_storage()
    except:
        traceback.print_exc()
        print(body)

    ch.basic_ack(delivery_tag=method.delivery_tag)
    return


logging.info(__file__ + ' is ready')
while True:
    try:
        if connection is None or channel is None:
            connection,channel = rabbit_init()

        channel.basic_consume(callback,queue=queue_name)    # ,no_ack=True
        channel.start_consuming()
    except (pika.exceptions.ConnectionClosed,pika.exceptions.AMQPConnectionError):
        logging.error('connection closed')  # connection to the local exchange closed? wut?
        connection,channel = None,None
        time.sleep(2)
    except KeyboardInterrupt:
        logging.info('user interrupted')
        break
    except:
        logging.exception(traceback.format_exc())
    
logging.info(__file__ + ' terminated')
