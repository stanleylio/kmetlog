import MySQLdb
from importlib import import_module






assert False






class storage(object):
    def __init__(self,user,password,dbname):
        self._dbname = dbname
        self._conn = MySQLdb.connect(host='localhost',
                                     user=user,
                                     passwd=password,
                                     db=dbname)
        self._cur = self._conn.cursor()

    def get_list_of_tables(self):
        self._cur.execute('SHOW TABLES;')
        return [tmp[0] for tmp in self._cur.fetchall()]

    def get_list_of_columns(self,table):
        self._cur.execute('SELECT * FROM {}.`{}` LIMIT 2;'.format(self._dbname,table))
        return [tmp[0] for tmp in self._cur.description]

    def insert(self,table,sample):
        table = '{}.`{}`'.format(self._dbname,table)
        cur = self._conn.cursor()

        for k in sample:
            # text/string/char value(s) must be in quote
            if type(sample[k]) in [str,unicode]:
                sample[k] = "'{}'".format(sample[k])
        
        sample = [(k,v) for k,v in sample.iteritems()]
        cols,vals = zip(*sample)
        vals = [str(tmp) for tmp in vals]
        cmd = 'INSERT INTO {table} ({cols}) VALUES ({vals})'.\
              format(table=table,
                     cols=','.join(cols),
                     vals=','.join(vals))
        #print(cmd)
        self._cur.execute(cmd)
        self._conn.commit()

    def read_time_range(self,table,column,begin,end,time_col='ts'):
        time_range = 'WHERE {time_col} BETWEEN "{begin}" AND "{end}"'.\
                     format(time_col=time_col,begin=begin,end=end)
        cmd = 'SELECT {time_col},{column} FROM {db}.`{table}` {time_range}'.\
                format(time_col=time_col,
                       column=column,
                       db=self._dbname,
                       table=table,
                       time_range=time_range)
        #print(cmd)
        self._cur.execute(cmd)
        return list(self._cur.fetchall())


if '__main__' == __name__:

    def get_schema(nodeconfig):
        C = import_module(nodeconfig.replace('-','_'))
        return [(c['dbtag'],c.get('dbtype','DOUBLE')) for c in C.conf]


    from os.path import expanduser
    password = open(expanduser('~/mysql_cred')).read().strip()
    dbname = 'kmetlog'
    
    conn = MySQLdb.connect(host='localhost',
                                 user='root',
                                 passwd=password,
                                 db=dbname)
    cur = conn.cursor()

    # create the specified table
    table = 'met'
    configfile = 'config.met'
    tmp = ','.join([' '.join(tmp) for tmp in get_schema(configfile)])
    cmd = 'CREATE TABLE IF NOT EXISTS {} ({})'.format('{}.`{}`'.format(dbname,table),tmp)
    print(cmd)
    cur.execute(cmd)

    print('- - - - -')
    import time
    store = storage('root',open('/home/pi/mysql_cred').read().strip(),'kmetlog')
    #print(store.get_list_of_columns('met'))
    print(store.read_time_range('met','PAR_V',time.time()-100,time.time()))
