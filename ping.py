# Upload past hour average of all variables go glazerlab-i7nuc
# Just to keep an eye on things since the promise of a web
# server on the KM was never delivered.
#
# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved. 2017
from __future__ import division
import sys,time,json,traceback
from os.path import expanduser
sys.path.append(expanduser('~'))
from kmetlog import dbstuff
from node.helper import ts2dt
from node.send2server import post
from kmetlog.storage import storage


store = storage('www-data',open('/var/www/km1app/km1app/mysql_cred').read().strip(),'kmetlog')

D = {}
end = time.time()
begin = end - 3600
for table in store.get_list_of_tables():
    V = {}
    for column in store.get_list_of_columns(table):
        if column in ['ts','OpticalRain_weather_condition']:
            continue
        #print table,column
        try:
            r = store.read_time_range(table,column,begin,end)
            N = len(r)
            r = zip(*r)
            #V[column] = (max(r[0]),round(sum(r[1])/N,3))
            V[column] = (max(r[0]),round(sum(r[1])/N,3),N)
        except:
            pass
    D[table] = V

try:
    m = json.dumps(D,separators=(',',':'))
    print m
    print(post(m,'http://grogdata.soest.hawaii.edu/api/4'))
except:
    m = traceback.format_exc()
    print(post(m,'http://grogdata.soest.hawaii.edu/api/4'))
