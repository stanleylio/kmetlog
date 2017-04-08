# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved. 2017
import zmq,sys,json,traceback,time,math,MySQLdb
from os.path import expanduser
sys.path.append(expanduser('~'))
from datetime import datetime
from node.storage.storage2 import storage
from node.parse_support import parse_message,pretty_print
from node.zmqloop import zmqloop
from cred import cred


def init_storage():
    #store = storage(user='root',passwd=open(expanduser('~/mysql_cred')).read().strip(),dbname='uhcm')
    return storage(user='root',passwd=cred['mysql'],dbname='kmetlog')
store = init_storage()


def callback(m):
    global store
    try:
        tmp = m.split(',',1)  # ignore the "kmet1," part
        d = json.loads(tmp[1])
        table = d['tag']
        d = {k:d[k] for k in store.get_list_of_columns(table)}
        store.insert(table,d)
        print('= = = = = = = = = = = = = = =')
        pretty_print(d)
    except MySQLdb.OperationalError,e:
        if e.args[0] in (MySQLdb.constants.CR.SERVER_GONE_ERROR,MySQLdb.constants.CR.SERVER_LOST):
            store = init_storage()
    except:
        traceback.print_exc()
        print(m)
    

zmqloop(callback,topic=u'kmet1')
