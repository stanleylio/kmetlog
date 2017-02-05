# -*- coding: utf-8 -*-
name = 'kmet-bbb'
location = 'Meteorological mast on the Kilo Moana'
note = 'kmet-bbb'


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

conf = [
    {
        'dbtag':'ts',
        'dbtype':'DOUBLE NOT NULL', # DOUBLE if not specified
        'description':'Sampling time (POSIX Timestamp)',
        'plot':False,       # True if not specified
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
    {
        'dbtag':'PSP_mV',
    },
    {
        'dbtag':'PAR_V',
    },
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
    {
        'dbtag':'UltrasonicWind_apparent_speed_mps',
    },
    {
        'dbtag':'UltrasonicWind_apparent_direction_deg',
    },
    {
        'dbtag':'OpticalRain_weather_condition',
        'dbtype':'CHAR(2)'      # Not Float!
    },
    {
        'dbtag':'OpticalRain_instantaneous_mmphr',
    },
    {
        'dbtag':'OpticalRain_accumulation_mm',
    },
    {
        'dbtag':'BucketRain_accumulation_mm',
    },
    {
        'dbtag':'Rotronics_T_C',
    },
    {
        'dbtag':'Rotronics_RH_percent',
    },
    {
        'dbtag':'RMYRTD_T_C',
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
    {
        'dbtag':'RMYRTD_Fan_rpm',
    },
    {
        'dbtag':'Rotronics_Fan_rpm',
    },
]


if '__main__' == __name__:
    for c in conf:
        print '- - -'
        for k,v in c.iteritems():
            assert 'dbtag' in c
            # everything else is optional. dbtype default to DOUBLE
            print k, ':' ,v

