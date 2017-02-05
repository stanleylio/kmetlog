import MySQLdb
from importlib import import_module


def get_schema(nodeconfig):
    C = import_module(nodeconfig.replace('-','_'))
    return [(c['dbtag'],c.get('dbtype','DOUBLE')) for c in C.conf]


class storage(object):
    def __init__(self,user,password,dbname):
        self._dbname = dbname
        self._conn = MySQLdb.connect(host='localhost',
                                     user='root',
                                     passwd=password,
                                     db=dbname)
        self._cur = self._conn.cursor()

    def insert(self,table,sample):
        table = '{}.`{}`'.format(self._dbname,table)
        cur = self._conn.cursor()

        sample = [(k,v) for k,v in sample.iteritems()]
        cols,vals = zip(*sample)
        vals = [str(tmp) for tmp in vals]
        cmd = 'INSERT INTO {table} ({cols}) VALUES ({vals})'.\
              format(table=table,
                     cols=','.join(cols),
                     vals=','.join(vals))
        #print cmd
        self._cur.execute(cmd)
        self._conn.commit()

    def get_column_names(self,table):
        self._cur.execute('SELECT * FROM {}.`{}`;'.format(self._dbname,table))
        return [tmp[0] for tmp in self._cur.description]


if '__main__' == __name__:
    from os.path import expanduser
    password = open(expanduser('~/mysql_cred')).read().strip()
    dbname = 'kmetlog'
    
    conn = MySQLdb.connect(host='localhost',
                                 user='root',
                                 passwd=password,
                                 db=dbname)
    cur = conn.cursor()

    # create the specified table
    table = 'kmet-bbb'
    configfile = 'config.kmet_bbb'
    tmp = ','.join([' '.join(tmp) for tmp in get_schema(configfile)])
    cmd = 'CREATE TABLE IF NOT EXISTS {} ({})'.format('{}.`{}`'.format(dbname,table),tmp)
    print(cmd)
    cur.execute(cmd)
