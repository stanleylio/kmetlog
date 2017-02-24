#private_key_file = '/root/.ssh/id_rsa'
#subscribeto = ['localhost:9002']
#data_dir = '/var/kmetlog/data'
#log_dir = '/var/kmetlog/log'
service_discovery_port = 9005
#realtime_port = 9007

# ADAM-4017
DAQ_HV_PORT = ('/dev/ttyUSB0',7,9600)    # serial port to DAQ, its RS485 ID, and baud rate
# ADAM-4018
DAQ_LV_PORT = ('/dev/ttyUSB1',5,9600)
# ADAM-4080
DAQ_F_PORT = ('/dev/ttyUSB2',4,9600)

DAQ_CH_MAP = {'PIR_mV':0,
              'PIR_case_V':1,
              'PIR_dome_V':2,
              'PSP_mV':1,
              'PAR_V':0,
              'BucketRain_accumulation_mm':3,
              'Rotronics_T':6,
              'Rotronics_RH':7,
              'RMYRTD_T':5,
              'Rotronics_Fan_rpm':0,
              'RMYRTD_Fan_rpm':1,
              }

USWIND_PORT = ('/dev/ttyUSB4',9600)
OPTICALRAIN_PORT = ('/dev/ttyUSB6',1200)
