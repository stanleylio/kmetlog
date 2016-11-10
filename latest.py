# show the latest reading in the database
# for debugging use
import time,sys
from os.path import expanduser
sys.path.append(expanduser('~/kmetlog'))
sys.path.append(expanduser('~/node'))
import dbstuff  # so there's no way to access the db without prior knowledge of the schema?
from sqlalchemy import create_engine,MetaData
from sqlalchemy.orm.session import Session
#from sqlalchemy.engine import reflection
#import numpy as np
from sqlalchemy import inspect
from sqlalchemy.orm import class_mapper
from datetime import datetime,timedelta
from helper import dt2ts


dbname = 'kmetlog'
engine = create_engine('mysql+mysqldb://root:' + open(expanduser('~/mysql_cred')).read() + '@localhost/' + dbname)
meta = dbstuff.Base.metadata
meta.bind = engine
#meta = MetaData()
#meta = MetaData(engine,reflect=True)
#print meta
#print
#print dbstuff.BME280_Sample.__table__.columns

session = Session(bind=engine)




'''insp = reflection.Inspector.from_engine(engine)
for table in insp.get_table_names():
    print table
    for c in insp.get_columns(table):
        print '\t', c
    print

exit()'''


'''print

for table in meta.tables:
    print table
    #print meta.tables[table].c
    print session.query(meta.tables[table]).order_by().first()
    print
#.filter(dbstuff.BME280_Sample.ts >= time.time()-600).all()

exit()'''


#r = engine.execute('SELECT * FROM BME280 ORDER BY ts DESC LIMIT 1;')
#for x in r:
#    print x
#exit()


insp = inspect(engine)

while True:
    try:
        print('\x1b[2J\x1b[;H')
        
        for table in insp.get_table_names():
            print table
        #    for c in insp.get_columns(table):
        #        print '\t', c['name']
                #print session.query(c).first()
                #print [prop for prop in class_mapper(dbstuff.BME280_Sample).iterate_properties]
            for r in engine.execute('SELECT * FROM ' + table + ' ORDER BY ts DESC LIMIT 1;'):
                print '\t', timedelta(seconds=dt2ts() - r['ts']), ','.join([str(v) for v in r])
                
            print
        time.sleep(5)
    except KeyboardInterrupt:
        break

exit()

# how do you iterate through all columns of all tables in the database via sqlalchemy?
# esp. if reflection is used (no prior knowledge of schema)


#print inspect(dbstuff.BME280_Sample)



#for table in meta.tables:
#    print table

#print
#print session.query(dbstuff.BME280_Sample).first()


#tags = [table.name for table in meta.sorted_tables]
#res = session.query(dbstuff.BME280_Sample).\
#      filter(dbstuff.BME280_Sample.ts >= time.time()-3600).all()
res = session.query(dbstuff.BME280_Sample)\
      .filter(dbstuff.BME280_Sample.P != None)\
      .order_by(dbstuff.BME280_Sample.ts)\
      .first()
print res.ts,res.P

#print
#for r in res:
#    print r.ts,r.P,r.T,r.RH

