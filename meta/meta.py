from __future__ import division
import subprocess,time,psutil
import sys
from os.path import expanduser
sys.path.append(expanduser('~'))
from node.storage.storage2 import storage,create_table


store = storage(dbname='kmetlog')

conf = [
    {
        'dbtag':'ts'
    },
    {
        'dbtag':'total'
    },
    {
        'dbtag':'used'
    },
    {
        'dbtag':'free'
    },
    ]

create_table(conf,'_meta',dbname='kmetlog')
print store.get_list_of_tables()

r = psutil.disk_usage('/')
print '{},{},{},{}'.format(time.time(),r.total,r.used,r.free)
store.insert('_meta',{'ts':time.time(),
                      'total':r.total,
                      'used':r.used,
                      'free':r.free
                      })
exit()
# in Python 3.3+, use shutil.disk_usage() instead


def execute(cmdaslist):
    p = subprocess.Popen(cmdaslist,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out,err = p.communicate()
    return out,err


out,_ = execute(['df'])
for row in out.strip().split('\n'):
    if row.endswith('/'):
        row = filter(lambda x: len(x),row.split(' '))
        total,used = row[1],row[3]

print '{},{},{}'.format(time.time(),total,used)
