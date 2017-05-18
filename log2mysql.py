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


def init_storage():
    return storage(user='root',passwd=cred['mysql'],dbname='kmetlog')
store = init_storage()


credentials = pika.PlainCredentials('nuc',cred['rabbitmq'])
connection = pika.BlockingConnection(pika.ConnectionParameters('166.122.96.12',5672,'/',credentials))
channel = connection.channel()
channel.exchange_declare(exchange=exchange,type='topic',durable=True)
result = channel.queue_declare(queue=basename(__file__),
                               durable=False,
                               exclusive=True,
                               auto_delete=True,
                               arguments={'x-message-ttl':10*1000})
channel.basic_qos(prefetch_count=1)
queue_name = result.method.queue
channel.queue_bind(exchange=exchange,
                   queue=queue_name,
                   routing_key='samples')


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
channel.basic_consume(callback,queue=queue_name)    # ,no_ack=True
try:
    channel.start_consuming()
except KeyboardInterrupt:
    logging.info('user interrupted')
logging.info(__file__ + ' terminated')
