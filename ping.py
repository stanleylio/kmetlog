import sys,socket
from os.path import expanduser
sys.path.append(expanduser('~'))
from kmetlog import dbstuff
from node.helper import ts2dt
from node.send2server import post
from sqlalchemy import create_engine
from sqlalchemy import inspect


#m = socket.gethostname()
#print(post(m,'http://grogdata.soest.hawaii.edu/api/4'))

dbname = 'kmetlog'
engine = create_engine('mysql+mysqldb://root:' + open(expanduser('~/mysql_cred')).read() + '@localhost/' + dbname)
meta = dbstuff.Base.metadata
meta.bind = engine

insp = inspect(engine)

d = []
for table in insp.get_table_names():
    #print table
    for r in engine.execute('SELECT FROM_UNIXTIME(ts) FROM ' + table + ' ORDER BY ts DESC LIMIT 1;'):
#        for k in r.keys():
#            print '\t{}\t{}'.format(k,r[k])
        #d.append({k:r[k] for k in r.keys()})
        d.append('{}:{}'.format(table,(ts2dt() - r['FROM_UNIXTIME(ts)']).total_seconds()))

m = ','.join(d)
print m
print(post(m,'http://grogdata.soest.hawaii.edu/api/4'))
