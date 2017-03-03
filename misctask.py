import sys,logging,traceback,time
#from drivers.Adafruit_BME280 import *
from drivers.watchdog import reset_auto
from config.config_support import import_node_config
from adam4080 import ADAM4080


config = import_node_config()


def initdaqf():
    logging.debug('Initializing frequency counter DAQ')
    daq = ADAM4080('{:02d}'.format(config.DAQ_F_PORT[1]),config.DAQ_F_PORT[0],config.DAQ_F_PORT[2])
    if not daq.CheckModuleName():
        logging.critical('Cannot reach the ADAM frequency counter.')
        return
    return daq


def taskMisc(send):
    try:
        fc = ADAM4080('{:02d}'.format(config.DAQ_F_PORT[1]),config.DAQ_F_PORT[0],config.DAQ_F_PORT[2])
        if not fc.CheckModuleName():
            logging.critical('Cannot reach the ADAM frequency counter.')
            return
        f0 = fc.ReadFrequency(0)
        f1 = fc.ReadFrequency(1)
        # the radiation shield fan gives two pulses per revolution.
        # so RPM = Hz/2*60
        send({'tag':'Misc',
             'ts':time.time(),
             'Rotronics_Fan_rpm':f0/2*60,   # rotronics humidity shield
             'RMYRTD_Fan_rpm':f1/2*60,      # RMY RTD shield
             })
    except:
        logging.exception(traceback.format_exc())


'''def taskBME280(send):
    try:
        bme = BME280_sl(bus=2,mode=BME280_OSAMPLE_16)
        r = bme.read()
        if r is not None:
            d = {'tag':'BME280',
                 'ts':time.time(),
                 'T':r['t'],
                 'P':r['p'],
                 'RH':r['rh']}
            send(d)
        else:
            logging.warning('Unable to read BME280')
    except:
        logging.warning('Exception in taskBME280():')
        logging.error(traceback.format_exc())'''


def taskWDT():
    try:
        good = reset_auto()
        if good:
            logging.info('WDT good')
        else:
            logging.warning('WDT not found')
    except:
        logging.error(traceback.format_exc())
