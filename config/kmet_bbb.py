subscribeto = ['localhost:9002','192.168.1.167:9002']
private_key_file = '/root/.ssh/id_rsa'
data_dir = '/var/kmetlog/data'
log_dir = '/var/kmetlog/log'
service_discovery_port = 9005
realtime_port = 9007


DAQ_HV_PORT = ('/dev/ttyUSB0',1)    # serial port to DAQ, and its RS485 ID
DAQ_LV_PORT = ('/dev/ttyUSB1',2)
DAQ_F_PORT = ('/dev/ttyUSB2',3)

# or record all channels and map later?
DAQ_CHANNEL_MAP = {'PIR_mV':('LV',2),
                   'PIR_case_V':('HV',6),
                   'PIR_dome_V':('HV',7),
                   'PSP_mV':('LV',5),
                   'PAR_V':('HV',5),
                   'BucketRain_accumulation_mm':('HV',0),
                   'Rotronics_T':('HV',1),
                   'Rotronics_RH':('HV',2),
                   'RMYRTD_T':('HV',3),
                   'Rotronics_Fan_rpm':('F',0),
                   'RMYRTD_Fan_rpm':('F',1),
                   }

conf = {}

tmp = [
    {
        'dbtag':'ts',
        'dbtype':'DOUBLE NOT NULL', # DOUBLE if not specified
        'description':'Sampling time (POSIX Timestamp)',
    },
    {
        'dbtag':'PIR_mV',
    },
    {
        'dbtag':'PIR_case_V',
    },
    {
        'dbtag':'PIR_dome_V',
    },
]
conf['PIR'] = tmp

tmp = [
    {
        'dbtag':'ts',
        'dbtype':'DOUBLE NOT NULL',
    },
    {
        'dbtag':'PSP_mV',
    },
]
conf['PSP'] = tmp

tmp = [
    {
        'dbtag':'ts',
        'dbtype':'DOUBLE NOT NULL',
    },
    {
        'dbtag':'PAR_V',
    },
]
conf['PAR'] = tmp

tmp = [
    {
        'dbtag':'ts',
        'dbtype':'DOUBLE NOT NULL',
    },
    {
        'dbtag':'UltrasonicWind_apparent_speed_mps',
    },
    {
        'dbtag':'UltrasonicWind_apparent_direction_deg',
    },
]
conf['UltrasonicWind'] = tmp

tmp = [
    {
        'dbtag':'ts',
        'dbtype':'DOUBLE NOT NULL',
    },
    {
        'dbtag':'OpticalRain_weather_condition',
        'dbtype':'CHAR(2)'      # Not a number!
    },
    {
        'dbtag':'OpticalRain_instantaneous_mmphr',
    },
    {
        'dbtag':'OpticalRain_accumulation_mm',
    },
]
conf['OpticalRain'] = tmp

tmp = [
    {
        'dbtag':'ts',
        'dbtype':'DOUBLE NOT NULL',
    },
    {
        'dbtag':'BucketRain_accumulation_mm',
    },
]
conf['BucketRain'] = tmp

tmp = [
    {
        'dbtag':'ts',
        'dbtype':'DOUBLE NOT NULL',
    },
    {
        'dbtag':'Rotronics_T_C',
    },
    {
        'dbtag':'Rotronics_RH_percent',
    },
]
conf['Rotronics'] = tmp

tmp = [
    {
        'dbtag':'ts',
        'dbtype':'DOUBLE NOT NULL',
    },
    {
        'dbtag':'RMYRTD_T_C',
    },
]
conf['RMYRTD'] = tmp

tmp = [
    {
        'dbtag':'ts',
        'dbtype':'DOUBLE NOT NULL',
    },
    {
        'dbtag':'BME280_T_C',
    },
    {
        'dbtag':'BME280_P_kPa',
    },
    {
        'dbtag':'BME280_RH_percent',
    },
]
conf['BME280'] = tmp

tmp = [
    {
        'dbtag':'ts',
        'dbtype':'DOUBLE NOT NULL',
    },
    {
        'dbtag':'RMYRTD_Fan_rpm',
    },
    {
        'dbtag':'Rotronics_Fan_rpm',
    },
]
conf['Misc'] = tmp


#    {
#        'dbtag':'PortWind_apparent_speed_mps',
#    },
#    {
#        'dbtag':'PortWind_apparent_direction_deg',
#    },
#    {
#        'dbtag':'StarboardWind_apparent_speed_mps',
#    },
#    {
#        'dbtag':'StarboardWind_apparent_direction_deg',
#    },


if '__main__' == __name__:
    for table in sorted(conf):
        print '- - -'
        print table
        for column in conf[table]:
            assert 'dbtag' in column
            # everything else is optional. dbtype default to DOUBLE
            print '\t' + column['dbtag']

    import MySQLdb
    from os.path import expanduser
    password = open(expanduser('~/mysql_cred')).read().strip()
    dbname = 'kmetlog'
    conn = MySQLdb.connect(host='localhost',
                                 user='root',
                                 passwd=password,
                                 db=dbname)
    cur = conn.cursor()

    # conf: a dictionary; one table per key;
    # each key maps to a list of dictionaries: {'dbtag':...} is mandatory; everything else is optional.
    # 'dbtype' defaults to DOUBLE

    for table in sorted(conf):
        tmp = ','.join([' '.join(tmp) for tmp in [(column['dbtag'],column.get('dbtype','DOUBLE')) for column in conf[table]]])
        cmd = 'CREATE TABLE IF NOT EXISTS {} ({})'.format('{}.`{}`'.format(dbname,table),tmp)
        print(cmd)
        #cur.execute(cmd)
