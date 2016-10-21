import sys,logging,traceback
from drivers.Adafruit_BME280 import *
from drivers.watchdog import Watchdog
from adam4080 import ADAM4080
sys.path.append(r'../node')
from helper import dt2ts


def taskMisc(send):
    try:
        fc = ADAM4080('03','/dev/ttyUSB2',9600)
        if not fc.CheckModuleName():
            logging.critical('Cannot reach the ADAM Frequency Counter at 03.')
            return
        f0 = fc.ReadFrequency(0)
        f1 = fc.ReadFrequency(1)
        # the radiation shield fan gives two pulses per revolution.
        # so RPM = Hz/2*60
        d = {'tag':'Misc',
             'ts':dt2ts(),
             'RadFan1_rpm':f0/2.0*60.0,     # rotronics humidity shield
             'RadFan2_rpm':f1/2.0*60.0,     # RMY RTD shield
             }
        send(d)
    except:
        logging.warning('Exception in taskMisc():')
        logging.error(traceback.format_exc())


def taskBME280(send):
    try:
        bme = BME280_sl(bus=2,mode=BME280_OSAMPLE_16)
        r = bme.read()
        if r is not None:
            d = {'tag':'BME280',
                 'ts':dt2ts(),
                 'T':r['t'],
                 'P':r['p'],
                 'RH':r['rh']}
            send(d)
        else:
            logging.warning('Unable to read BME280')
    except:
        logging.warning('Exception in taskBME280():')
        logging.error(traceback.format_exc())


def taskWDT():
    try:
        good = False
        for bus in [1,2]:
            try:
                for i in range(3):
                    w = Watchdog(bus=bus)
                    w.reset()
                good = True
                #print('Found watchdog on bus {}'.format(bus))
            except:
                #logger.debug(e)
                pass
                # the WDT is either on bus 1 or bus 2, so there WILL be one exception
                # if I log it, I would have to specify which I2C bus to avoid false negative;
                # if I don't log it, I risk missing other exceptions...
        if good:
            logging.info('WDT good')
        else:
            logging.warning('WDT not found')
    except:
        logging.error(traceback.format_exc())
