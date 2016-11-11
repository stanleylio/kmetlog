from sqlalchemy import create_engine,Table,Column,MetaData,Integer
from sqlalchemy.types import Float,String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()


class PIR_Sample(Base):
    __tablename__ = 'PIR'
    id = Column('id',Integer,primary_key=True)
    ts = Column('ts',Float(precision=32))
    ir_mV = Column('ir_mV',Float(precision=32))
    t_case_V = Column('t_case_V',Float(precision=32))
    t_dome_V = Column('t_dome_V',Float(precision=32))

    def __repr__(self):
        return str(self.__dict__)

class PSP_Sample(Base):
    __tablename__ = 'PSP'
    id = Column('id',Integer,primary_key=True)
    ts = Column('ts',Float(precision=32))
    psp_mV = Column('psp_mV',Float(precision=32))

    def __repr__(self):
        return str(self.__dict__)

class PAR_Sample(Base):
    __tablename__ = 'PAR'
    id = Column('id',Integer,primary_key=True)
    ts = Column('ts',Float(precision=32))
    par_V = Column('par_V',Float(precision=32))

    def __repr__(self):
        return str(self.__dict__)

class PortWind_Sample(Base):
    __tablename__ = 'PortWind'
    id = Column('id',Integer,primary_key=True)
    ts = Column('ts',Float(precision=32))
    apparent_speed_mps = Column('apparent_speed_mps',Float(precision=32))
    apparent_direction_deg = Column('apparent_direction_deg',Float(precision=32))

    def __repr__(self):
        return str(self.__dict__)

class StarboardWind_Sample(Base):
    __tablename__ = 'StarboardWind'
    id = Column('id',Integer,primary_key=True)
    ts = Column('ts',Float(precision=32))
    apparent_speed_mps = Column('apparent_speed_mps',Float(precision=32))
    apparent_direction_deg = Column('apparent_direction_deg',Float(precision=32))

    def __repr__(self):
        return str(self.__dict__)

class UltrasonicWind_Sample(Base):
    __tablename__ = 'UltrasonicWind'
    id = Column('id',Integer,primary_key=True)
    ts = Column('ts',Float(precision=32))
    apparent_speed_mps = Column('apparent_speed_mps',Float(precision=32))
    apparent_direction_deg = Column('apparent_direction_deg',Float(precision=32))

    def __repr__(self):
        return str(self.__dict__)

class OpticalRain_Sample(Base):
    __tablename__ = 'OpticalRain'
    id = Column('id',Integer,primary_key=True)
    ts = Column('ts',Float(precision=32))
    weather_condition = Column('weather_condition',String(2))  # Not Float!
    instantaneous_mmphr = Column('instantaneous_mmphr',Float(precision=32))
    accumulation_mm = Column('accumulation_mm',Float(precision=32))

    def __repr__(self):
        return str(self.__dict__)

class BucketRain_Sample(Base):
    __tablename__ = 'BucketRain'
    id = Column('id',Integer,primary_key=True)
    ts = Column('ts',Float(precision=32))
    accumulation_mm = Column('accumulation_mm',Float(precision=32))

    def __repr__(self):
        return str(self.__dict__)

class Rotronics_Sample(Base):
    __tablename__ = 'Rotronics'
    id = Column('id',Integer,primary_key=True)
    ts = Column('ts',Float(precision=32))
    T = Column('T',Float(precision=32))
    RH = Column('RH',Float(precision=32))

    def __repr__(self):
        return str(self.__dict__)

class RMYRTD_Sample(Base):
    __tablename__ = 'RMYRTD'
    id = Column('id',Integer,primary_key=True)
    ts = Column('ts',Float(precision=32))
    T = Column('T',Float(precision=32))

    def __repr__(self):
        return str(self.__dict__)

class BME280_Sample(Base):
    __tablename__ = 'BME280'
    id = Column('id',Integer,primary_key=True)
    ts = Column('ts',Float(precision=32))
    T = Column('T',Float(precision=32))
    P = Column('P',Float(precision=32))
    RH = Column('RH',Float(precision=32))

    def __repr__(self):
        return str(self.__dict__)

class Misc_Sample(Base):
    __tablename__ = 'Misc'
    id = Column('id',Integer,primary_key=True)
    ts = Column('ts',Float(precision=32))
    RadFan1_rpm = Column('RadFan1_rpm',Float(precision=32))
    RadFan2_rpm = Column('RadFan2_rpm',Float(precision=32))

    def __repr__(self):
        return str(self.__dict__)



if '__main__' == __name__:
    engine = create_engine('mysql+mysqldb://root:otg_km!@localhost',
                           pool_recycle=3600,
                           echo=True)
    dbname = 'kmetlog'
    engine.execute('CREATE DATABASE IF NOT EXISTS ' + dbname)
    engine.execute('USE ' + dbname)
    Base.metadata.create_all(engine)

    #Session = sessionmaker()
    #Session.configure(bind=engine)

    #session = Session()
    #ms = MetSample(blah...)
    #session.add(ms)

    #def addSample(ms):
        #session.add(ms)
        #session.commit()

