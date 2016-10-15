# Periodically read the sensors and publish via TCP
#
#
# Putting all polling in one process:
#   Pros: all code in one place
#       no multiple ports to subscribe to for clients
#       no multiple processes to manage
#       a single log file
#   Cons:
#       one slow task can slow/block everything else
# 
# Ocean Technology Group
# SOEST, University of Hawaii
# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved, 2016
import sys,zmq,logging,json,time,traceback,serial
import logging.handlers
sys.path.append(r'../node')
from helper import *
from random import random
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from datetime import datetime,timedelta
from drivers.Adafruit_BME280 import *
from adam4018 import ADAM4018
from os import makedirs
from os.path import exists,join
#from r2t import r2t
import config
from drivers.watchdog import Watchdog


log_path = '/var/logging/log'
if not exists(log_path):
    makedirs(log_path)

#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.handlers.RotatingFileHandler(join(log_path,'read_sensors.log'),
                                          maxBytes=1e7,
                                          backupCount=10)
fh.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
logging.Formatter.converter = time.gmtime
formatter = logging.Formatter('%(asctime)s,%(name)s,%(levelname)s,%(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


def initdaqhv():
    logger.debug('Initialize high-volt DAQ')
    daq = ADAM4018('01','/dev/ttyUSB0',9600)
    if not daq.CheckModuleName():
        logger.critical('Cannot reach the DAQ (HV) at 01.')
        return None
    if not any([daq.SetInputRange(2.5) for tmp in range(3)]):
        logger.critical('Unable to set DAQ (HV) input range.')
        return None
    return daq

def initdaqlv():
    logger.debug('Initialize low-volt DAQ')
    daq = ADAM4018('02','/dev/ttyUSB1',9600)
    if not daq.CheckModuleName():
        logger.critical('Cannot reach the DAQ (LV) at 02.')
        return None
    if not any([daq.SetInputRange(50e-3) for tmp in range(3)]):
        logger.critical('Unable to set DAQ (LV) input range.')
        return None
    return daq


logger.debug('binding 0MQ port...')
#zmq_port = 'tcp://*:9002'
zmq_port = 'tcp://*:' + str(config.kmet1_port)
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind(zmq_port)
logger.info('Broadcasting at {}'.format(zmq_port))


last_transmitted = datetime.utcnow()
def send(d):
    try:
        if 'tag' in d:
            topic = d['tag']
            s = json.dumps(d,separators=(',',':'))
            s = 'kmet1_{topic},{msg}'.format(msg=s,topic=topic)
            logger.debug(s)
        else:
            s = ''
        global last_transmitted
        last_transmitted = datetime.utcnow()
        socket.send_string(s)
    except:
        logger.error(traceback.format_exc())


daqhv = None
daqlv = None
# there gotta be a way to decouple these. TODO
def taskDAQ():
    """Poll the DAQ stuff: PAR, PSP, PIR and its thermistors"""
    global daqhv
    global daqlv
    
    par = psp = pir = None

    try:
        if daqhv is None:
            daqhv = initdaqhv()
        if daqhv is not None:
            r = daqhv.ReadAll()
            if r is not None:
                par = {'tag':'PAR',
                     'ts':dt2ts(datetime.utcnow()),
                     'par_V':2*r[5]}    # PAR connects to DAQ via a V/2 voltage divider (0.1% precision)
                send(par)

                pir = {'tag':'PIR',
                       'ts':dt2ts(datetime.utcnow()),
                       'ir_mV':r[2]/1e-3,   # will be overwritten if LV read is successful
                       't_case_V':r[6],
                       't_dome_V':r[7]}

                # bucket rain gauge
                bucket = {'tag':'BucketRain',
                          'ts':dt2ts(datetime.utcnow()),
                          'accumulation_mm':20*r[0]}    # map 0-2.5V to 0-50mm
                send(bucket)
            else:
                logger.error('Unable to read the DAQ')
                daqhv = None
        else:
            logger.error('DAQ (HV) initialization failed')
    except:
        logger.error(traceback.format_exc())

    try:
        if daqlv is None:
            daqlv = initdaqlv()
        if daqlv is not None:
            r = daqlv.ReadAll()
            if r is not None:
                psp = {'tag':'PSP',
                     'ts':dt2ts(datetime.utcnow()),
                     'psp_mV':r[5]/1e-3}
                send(psp)

                if pir is not None:
                    pir.update({'tag':'PIR',
                         'ts':dt2ts(datetime.utcnow()),
                         'ir_mV':r[2]/1e-3})
                else:
                    # HV DAQ read failed previously
                    logger.warning('PIR thermistor read failed')
                    pir = {'tag':'PIR',
                         'ts':dt2ts(datetime.utcnow()),
                         'ir_mV':r[2]/1e-3,
                         't_case_V':float('nan'),
                         't_dome_V':float('nan')}
                send(pir)

                # and what if THIS failed? TODO
            else:
                logger.error('Unable to read the DAQ (LV)')
                daqlv = None
        else:
            logger.error('DAQ (LV) initialization failed')
    except:
        logger.error(traceback.format_exc())


'''def taskPortWind():
    taskPortWind.dir = (taskPortWind.dir + 100*random()/10 - 5) % 360
    try:
        d = {'tag':'PortWind',
             'ts':dt2ts(datetime.utcnow()),
             'apparent_speed_mps':20*random(),
             'apparent_direction_deg':taskPortWind.dir}
        send(d)
    except Exception as e:
        logger.error(e)
taskPortWind.dir = 360*random()

def taskStarboardWind():
    try:
        d = {'tag':'StarboardWind',
             'ts':dt2ts(datetime.utcnow()),
             'apparent_speed_mps':20*random(),
             'apparent_direction_deg':360*random()}
        send(d)
    except Exception as e:
        logger.error(e)'''

def taskUltrasonicWind():
    try:
        with serial.Serial('/dev/ttyUSB7',9600,timeout=0.1) as s:
            #s.write('M0!\r')       # the sensor is slow at processing commands...
            s.write('M')
            s.write('0')
            s.write('!')
            s.write('\r')
            s.flushOutput()
            line = []
            for i in range(20):     # should be ~17 chr
                r = s.read(size=1)
                if len(r):
                    line.extend(r)
                if '\r' in line:
                    break
            #logger.debug(''.join(line))
            #logger.debug([ord(c) for c in line])
            line = ''.join(line).strip().split(' ')
            if '0' == line[0] and '*' == line[3][2]:    # '0' is the address of the sensor
                d = {'tag':'UltrasonicWind',
                     'ts':dt2ts(datetime.utcnow()),
                     'apparent_speed_mps':float(line[1]),
                     'apparent_direction_deg':float(line[2])}
                send(d)
            else:
                logger.error('Failed to read ultrasonic anemometer. {}'.format(line))
    except:
        logger.error(traceback.format_exc())


last_reset_day = datetime.utcnow().day
def taskOpticalRain():
    try:
        with serial.Serial('/dev/ttyUSB6',1200,timeout=1) as s:
            s.write('A')
            line = []
            for i in range(30):
                r = s.read(size=1)
                if len(r):
                    line.append(r)
                if '\r' in line:
                    break
            line = ''.join(line).rstrip()

            d = {'tag':'OpticalRain',
                 'ts':dt2ts(datetime.utcnow()),
                 'weather_condition':line[0:2],
                 'instantaneous_mmphr':float(line[3:7]),
                 'accumulation_mm':float(line[8:15])}
            send(d)

            # - - -

            ts = datetime.utcnow()
            global last_reset_day
            if not ts.day == last_reset_day:
                logging.info('Accumulation Data Reset')
                s.write('R')
                for i in range(10):
                    r = s.read()
                    if len(r):  # whatever it is, as long as the sensor responded
                        last_reset_day = ts.day
                        break
    except:
        logger.error(traceback.format_exc())


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
    except:
        logger.warning('Exception in taskBME280():')
        logger.error(traceback.format_exc())


def taskHeartbeat():
    try:
        if datetime.utcnow() - last_transmitted > timedelta(seconds=60):
            send({})
    except Exception as e:
        logger.error(e)

def taskBBBWatchdog():
    for bus in [1,2]:
        try:
            for i in range(3):
                w = Watchdog(bus=bus)
                w.reset()
            #print('Found watchdog on bus {}'.format(bus))
        except:
            #logger.debug(e)
            pass
            # if I log it, I would have to specify which I2C bus to avoid false negative;
            # if I don't log it, I risk missing real error...


logger.debug('starting tasks...')
lcdaq = LoopingCall(taskDAQ)
lcbme = LoopingCall(taskBME280)
#lcport = LoopingCall(taskPortWind)
#lcstbd = LoopingCall(taskStarboardWind)
lcultras = LoopingCall(taskUltrasonicWind)
lcoptical = LoopingCall(taskOpticalRain)
lchb = LoopingCall(taskHeartbeat)
lcwd = LoopingCall(taskBBBWatchdog)
lcdaq.start(10)
lcbme.start(60)
#lcport.start(1)
#lcstbd.start(1)
lcultras.start(1)
lcoptical.start(60)
lchb.start(1,now=False)
lcwd.start(60,now=False)

logger.debug('starting reactor()...')
reactor.run()
del daqhv
del daqlv
logging.info('Terminated')
