# Generate and publish random data for debugging
# 
# Ocean Technology Group
# SOEST, University of Hawaii
# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved, 2016
import sys,zmq,logging,json,time,traceback
import logging.handlers
sys.path.append(r'../node')
from helper import *
from drivers.Adafruit_BME280 import *
from random import random
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from datetime import datetime
from adam4018 import ADAM4018
from os import makedirs
from os.path import exists,join
from r2t import r2t


log_path = 'log'
if not exists(log_path):
    makedirs(log_path)


#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.handlers.RotatingFileHandler(join(log_path,'read_sensors.log'),
                                          maxBytes=1e8,
                                          backupCount=10)
fh.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logging.Formatter.converter = time.gmtime
formatter = logging.Formatter('%(asctime)s,%(name)s,%(levelname)s,%(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


def initdaqhv():
    daq = ADAM4018('01','/dev/ttyUSB0',9600)
    if not daq.CheckModuleName():
        logger.critical('Cannot reach the DAQ (HV) at 01.')
        return None
    if not any([daq.SetInputRange(2.5) for tmp in range(3)]):
        logger.critical('Unable to set DAQ (HV) input range.')
        return None
    return daq

def initdaqlv():
    daq = ADAM4018('02','/dev/ttyUSB0',9600)
    if not daq.CheckModuleName():
        logger.critical('Cannot reach the DAQ (LV) at 01.')
        return None
    if not any([daq.SetInputRange(50e-3) for tmp in range(3)]):
        logger.critical('Unable to set DAQ (LV) input range.')
        return None
    return daq


zmq_port = 'tcp://*:9002'
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind(zmq_port)
logger.info('Broadcasting at {}'.format(zmq_port))


def send(d):
    try:
        if 'tag' in d:
            topic = d['tag']
            s = json.dumps(d,separators=(',',':'))
            s = 'kmet1_{topic},{msg}'.format(msg=s,topic=topic)
            logger.debug(s)
        else:
            s = ''
        socket.send_string(s)
    except Exception as e:
        logger.error(e)
        #traceback.print_exc()


daqhv = None
daqlv = None

def taskDAQ():
    global daqhv
    global daqlv
    
    par = None
    psp = None
    pir = None
    
    if daqhv is None:
        daqhv = initdaqhv()
    if daqhv is not None:
        r = daqhv.ReadAll()
        if r is not None:
            par = {'tag':'PAR',
                 'ts':dt2ts(datetime.utcnow()),
                 'par_V':2*r[0]}    # PAR connects to DAQ via a V/2 voltage divider (0.1% precision)
            send(par)

            Vref = 2.5
            if Vref > r[6] and Vref > r[7]:  # TODO: also check for ZeroDivisionError
                r_case = 10e3*r[6]/(Vref-r[6])
                r_dome = 10e3*r[7]/(Vref-r[7])
                pir = {'tag':'PIR',
                       'ts':dt2ts(datetime.utcnow()),
                       't_case_ohm':r_case,
                       't_dome_ohm':r_dome,
                       't_case_degC':r2t(r_case),
                       't_dome_degC':r2t(r_dome)}
            else:
                logger.warning('V_thermistor >= Vref: {},{}'.format(r[6],r[7]))
        else:
            logger.error('Unable to read the DAQ')
            daqhv = None

    if daqlv is None:
        daqlv = initdaqlv()
    if daqlv is not None:
        r = daqlv.ReadAll()
        if r is not None:
            psp = {'tag':'PSP',
                 'ts':dt2ts(datetime.utcnow()),
                 'psp_mV':r[1]/1e-3}
            send(psp)

            if pir is not None:
                pir.update({'tag':'PIR',
                     'ts':dt2ts(datetime.utcnow()),
                     'ir_mV':r[2]/1e-3})
            else:
                pir = {'tag':'PIR',
                     'ts':dt2ts(datetime.utcnow()),
                     'ir_mV':r[2]/1e-3,
                     't_case_ohm':float('nan'),
                     't_dome_ohm':float('nan')}
            send(pir)
        else:
            logger.error('Unable to read the DAQ')
            daqlv = None
        
    
'''def taskPortWind():
    d = {'tag':'PortWind',
         'ts':dt2ts(datetime.utcnow()),
         'apparent_speed_mps':50*random(),
         'apparent_direction_deg':360*random()}
    send(d)

def taskStarboardWind():
    d = {'tag':'StarboardWind',
         'ts':dt2ts(datetime.utcnow()),
         'apparent_speed_mps':50*random(),
         'apparent_direction_deg':360*random()}
    send(d)

def taskUltrasonicWind():
    d = {'tag':'UltrasonicWind',
         'ts':dt2ts(datetime.utcnow()),
         'apparent_speed_mps':50*random(),
         'apparent_direction_deg':360*random()}
    send(d)

def taskOpticalRain():
    d = {'tag':'OpticalRain',
         'ts':dt2ts(datetime.utcnow()),
         'weather_condition':str(99*random()),
         'instantaneous_mmphr':100*random(),
         'accumulation_mm':1000*random()}
    send(d)
'''

def taskBME280():
    try:
        bme = BME280_sl(bus=2,mode=BME280_OSAMPLE_16)
        r = bme.read()
        if r is not None:
            d = {'tag':'BME280',
                 'ts':dt2ts(datetime.utcnow()),
                 'T':r['t'],
                 'P':r['p'],
                 'RH':r['rh']}
            send(d)
        else:
            logger.warning('Unable to read BME280')
    except Exception as e:
        logger.error(e)


def taskHeartbeat():
    send({})


lcdaq = LoopingCall(taskDAQ)
lcbme = LoopingCall(taskBME280)
lchb = LoopingCall(taskHeartbeat)
lcdaq.start(30,now=False)
lcbme.start(60,now=False)
lchb.start(1,now=True)


reactor.run()
del daqhv
del daqlv
logging.info('Terminated')
