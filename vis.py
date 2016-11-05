import time,sys
from os.path import expanduser
sys.path.append(expanduser('~/kmetlog'))
import dbstuff
from sqlalchemy import create_engine
#from sqlalchemy import create_engine,Table,MetaData
from sqlalchemy.orm import sessionmaker
import numpy as np


dbname = 'kmetlog'
engine = create_engine('mysql+mysqldb://root:' + open(expanduser('~/mysql_cred')).read().strip() + '@localhost',
                       pool_recycle=3600,
                       echo=False)
engine.execute('USE ' + dbname)
meta = dbstuff.Base.metadata
#meta = MetaData()
#BME280_Sample = Table('BME280',meta,autoload=True,autoload_with=engine)

Session = sessionmaker()
Session.configure(bind=engine)
session = Session()

for table in meta.tables:
    print table



#tags = [table.name for table in meta.sorted_tables]
res = session.query(dbstuff.BME280_Sample).\
      filter(dbstuff.BME280_Sample.ts >= time.time()-3600).all()

print
print dbstuff.BME280_Sample.__table__.columns

print 
for r in res:
    print r.ts,r.P,r.T,r.RH

