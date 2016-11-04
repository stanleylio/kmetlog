import sys,socket,time
from os.path import expanduser
sys.path.append(expanduser('~'))
from node.send2server import post
from os.path import expanduser
import dbstuff
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


m = socket.gethostname()
print(post(m,'http://grogdata.soest.hawaii.edu/api/4'))
exit()




dbname = 'kmetlog'
engine = create_engine('mysql+mysqldb://root:' + open(expanduser('~/mysql_cred')).read() + '@localhost',
                       pool_recycle=3600,
                       echo=False)
engine.execute('USE ' + dbname)
#dbstuff.Base.metadata.create_all(engine)
meta = dbstuff.Base.metadata

Session = sessionmaker()
Session.configure(bind=engine)
session = Session()

#tags = [table.name for table in meta.sorted_tables]
#res = session.query('BME280').all()
print session.query(dbstuff.BME280_Sample).\
      filter(dbstuff.BME280_Sample.ts >= time.time()-3600).all()

