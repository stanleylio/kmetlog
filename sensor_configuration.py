




conf = [{'name':'Anemometer (PORT)',
         'make':'RM Young',
         'model':'05106',
         'port':'/dev/ttyUSB0',
         'baud':9600},

        {'name':'Anemometer (STBD)',
         'make':'RM Young',
         'model':'05106',
         'port':'/dev/ttyUSB1',
         'baud':9600},

        {'name':'Ultrasonic Anemometer',
         'make':'RM Young',
         'model':'85106',
         'port':'/dev/ttyUSB2',
         'baud':9600},

        {'name':'Optical Rain Gauge',
         'make':'Optical Scientific Inc.',
         'model':'ORG-815-DR',
         'port':'/dev/ttyUSB3',
         'baud':1200},
        
        {'name':'PAR',  # what about the 0.5 scaling factor?
         'make':'Biospherical Instruments Inc.',
         'model':'QSR-2200',
         'daq':{'port':'/dev/ttyUSB4','baud':9600,'address':1,'channel':0,'input_range':2.5}},

        {'name':'PSP',
         'make':'Eppley Lab',
         'model':'PSP',
         'daq':{'port':'/dev/ttyUSB4','baud':9600,'address':1,'channel':1,'input_range':15e-3}},

        {'name':'PIR',
         'make':'Eppley Lab',
         'model':'PIR',
         'daq':{'port':'/dev/ttyUSB4','baud':9600,'address':1,'channel':2,'input_range':50e-3}},

        {'name':'PIR_case_thermistor',
         'make':'Eppley Lab',
         'model':'PIR',
         'daq':{'port':'/dev/ttyUSB4','baud':9600,'address':1,'channel':6,'input_range':2.5}},

        {'name':'PIR_dome_thermistor',
         'make':'Eppley Lab',
         'model':'PIR',
         'daq':{'port':'/dev/ttyUSB4','baud':9600,'address':1,'channel':7,'input_range':2.5}},

        {'name':'Rain Gauge',
         'make':'RM Young',
         'model':'50203',
         'daq':{'port':'/dev/ttyUSB4','baud':9600,'address':1,'channel':3,'input_range':2.5}},
        ]


if '__main__' == __name__:
    for c in conf:
        if 'port' in c and 'baud' in c:
            # it's addressible via serial
            print('{}, {}, {}'.format(c['name'],c['port'],c['baud']))
        elif 'daq' in c:
            # it's on a DAQ
            daq = c['daq']
            print('{}, {}, {}; CH{}, {}V'.format(c['name'],daq['port'],daq['baud'],daq['channel'],daq['input_range']))
    


