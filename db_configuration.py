# initialize a database with the proper tables and columns
# does nothing if the database already exists and has the same configuration
# not tested for database migration (when schema changes)
#
# Stanley H.I. Lio, 2016
# hlio@hawaii.edu
from sqlalchemy import create_engine,MetaData
from sqlalchemy import Table,Column,Integer,Float,String,Sequence


# a list; one entry per table.
# every entry is a dict(), with the 'name' of the table and the definition of 'columns'
schema = [{'name':'PIR',
      'columns':[('ir_mV',Float),('t_case_V',Float),('t_dome_V',Float)]},
     {'name':'PSP',
      'columns':[('psp_mV',Float)]},
     {'name':'PAR',
      'columns':[('par_V',Float)]},
     {'name':'PortWind',
      'columns':[('apparent_speed_mps',Float),('apparent_direction_deg',Float)]},
     {'name':'StarboardWind',
      'columns':[('apparent_speed_mps',Float),('apparent_direction_deg',Float)]},
     {'name':'UltrasonicWind',
      'columns':[('apparent_speed_mps',Float),('apparent_direction_deg',Float)]},
     {'name':'OpticalRain',
      'columns':[('weather_condition',String),('instantaneous_mmphr',Float),('accumulation_mm',Float)]},
     {'name':'BME280',
      'columns':[('T',Float),('P',Float),('RH',Float)]},
     # two more radiation shields and one more rain gauge
     ]


if '__main__' == __name__:
    #engine = create_engine('sqlite:///:memory:')
    engine = create_engine('sqlite:///data/met.db',echo=True)
    metadata = MetaData()

    # Generate a list of Table(s)
    # what's this mess?
    # http://docs.sqlalchemy.org/en/latest/core/metadata.html
    tables = []
    for t in schema:
        d = [t['name'],metadata]
        d.append(Column('id',Integer,Sequence('sample_id_seq'),primary_key=True))
        d.append(Column('ts',Float))
        d.extend([Column(*tmp) for tmp in t['columns']])
        tables.append(Table(*d))
    #print tables

    # basically the above two blocks do this for each table (using PSPSample as example):
    '''tables.append(
        Table('PSPSample',metadata,
              Column('id',Integer,Sequence('sample_id_seq'),primary_key=True),
              Column('ts',Float),
              Column('psp_mV',Float)
        )
    )'''

    # and metadata hides all the schema info. I hate magic.
    metadata.create_all(engine)

