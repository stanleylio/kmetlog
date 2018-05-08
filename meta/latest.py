# show the latest reading in the database
# for debugging use
import time,sys
from os.path import expanduser
sys.path.append(expanduser('~/kmetlog'))
sys.path.append(expanduser('~/node'))
from datetime import datetime,timedelta
import MySQLdb
from storage import storage


dbname = 'kmetlog'
store = storage('www-data',open('/var/www/km1app/km1app/mysql_cred').read().strip(),dbname)

S = {}
for table in store.get_list_of_tables():
    S[table] = store.get_list_of_columns(table)

conn = MySQLdb.connect(host='localhost',
                             user='www-data',
                             passwd=open('/var/www/km1app/km1app/mysql_cred').read().strip(),
                             db=dbname)
cur = conn.cursor()

while True:
    try:
        print('\x1b[2J\x1b[;H')
        for table in S:
            print(table)
            cur.execute('SELECT * FROM ' + table + ' ORDER BY ts DESC LIMIT 1;')
            for r in cur.fetchall():
                ago = time.time() - r[0]
                if ago < 0:
                    print('\t', timedelta(seconds=ago), ' ... STRANGE...')
                if ago < 5*60:
                    print('\t', timedelta(seconds=ago), ' ago') #, ','.join([str(v) for v in r])
                else:
                    print('\t', timedelta(seconds=ago), ' ago * * * * * STALE * * * * *')
                print('\t', r)

            # even for SELECT?
            # http://stackoverflow.com/questions/13287749/should-i-commit-after-a-single-select
            conn.commit()
                
            print()
        time.sleep(10)
    except KeyboardInterrupt:
        break
