# Periodically read the sensors and publish via zmq
# For kmet-bbb3
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
# University of Hawaii
# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved. 2017
from __future__ import division,print_function
import sys,zmq,logging,json,time,traceback,serial
import logging.handlers
from os.path import expanduser
sys.path.append(expanduser('~/node'))
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from datetime import datetime,timedelta
from adam4017 import ADAM4017
from adam4018 import ADAM4018
from misctask import initdaqf
#import service_discovery
from socket import gethostname
from misctask import taskWDT,taskMisc
from config.config_support import import_node_config


config = import_node_config()


#'DEBUG,INFO,WARNING,ERROR,CRITICAL'
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.handlers.SysLogHandler(address='/dev/log')
logger.addHandler(handler)


def initdaqhv():
    logging.debug('Initializing high-volt DAQ')
    daq = ADAM4017('{:02d}'.format(config.DAQ_HV_PORT[1]),config.DAQ_HV_PORT[0],config.DAQ_HV_PORT[2])
    if not daq.CheckModuleName():
        logging.critical('Cannot reach the DAQ (HV).')
        return None
    if not any([daq.SetInputRange(5) for tmp in range(3)]):   # any() is short-circuited
        logging.critical('Unable to set DAQ (HV) input range.')
        return None
    return daq

def initdaqlv():
    logging.debug('Initializing low-volt DAQ')
    daq = ADAM4018('{:02d}'.format(config.DAQ_LV_PORT[1]),config.DAQ_LV_PORT[0],config.DAQ_LV_PORT[2])
    if not daq.CheckModuleName():
        logging.critical('Cannot reach the DAQ (LV).')
        return None
    if not any([daq.SetInputRange(50e-3) for tmp in range(3)]):
        logging.critical('Unable to set DAQ (LV) input range.')
        return None
    return daq


logger.info('Checking HV DAQ: ID{:02d} on {} at {}...'.format(config.DAQ_HV_PORT[1],config.DAQ_HV_PORT[0],config.DAQ_HV_PORT[2]))
logger.info('PASS' if initdaqhv() is not None else 'FAIL')
logger.info('Checking LV DAQ: ID{:02d} on {} at {}...'.format(config.DAQ_LV_PORT[1],config.DAQ_LV_PORT[0],config.DAQ_LV_PORT[2]))
logger.info('PASS' if initdaqlv() is not None else 'FAIL')
logger.info('Checking F DAQ: ID{:02d} on {} at {}...'.format(config.DAQ_F_PORT[1],config.DAQ_F_PORT[0],config.DAQ_F_PORT[2]))
logger.info('PASS' if initdaqf() is not None else 'FAIL')


logger.debug('binding 0MQ port...')
zmq_port = 'tcp://*:9002'
context = zmq.Context()
zsocket = context.socket(zmq.PUB)
zsocket.bind(zmq_port)
logger.info('Broadcasting at {}'.format(zmq_port))


def send(d):
    try:
        if 'tag' in d:
            topic = d['tag']
            s = json.dumps(d,separators=(',',':'))
            s = 'kmet1_{topic},{msg}'.format(msg=s,topic=topic)
            logger.info(s)
        else:
            s = ''
        send.last_transmitted = datetime.utcnow()
        zsocket.send_string(s)
    except:
        logger.error(traceback.format_exc())
send.last_transmitted = datetime.utcnow()


daqhv = None
daqlv = None
# there gotta be a way to decouple these. TODO
def taskDAQ():
    global daqhv
    global daqlv

    try:
        if daqhv is None:
            daqhv = initdaqhv()
        rhv = daqhv.ReadAll()
        if rhv is None:
            logger.error('Unable to read HV DAQ')
            daqhv = None
            return
            
        ts = time.time()

        send({'tag':'PAR',
               'ts':ts,
               'PAR_V':rhv[config.DAQ_CH_MAP['PAR_V']]})

        send({'tag':'Rotronics',
              'ts':ts,
              'Rotronics_T_C':rhv[config.DAQ_CH_MAP['Rotronics_T_C']]*100 - 30, # from Volt to Deg.C
              'Rotronics_RH_percent':rhv[config.DAQ_CH_MAP['Rotronics_RH_percent']]*100})   # %RH

        send({'tag':'RMYRTD',
              'ts':ts,
              'RMYRTD_T_C':rhv[config.DAQ_CH_MAP['RMYRTD_T_C']]*100 - 50})  # [0,1] V maps to [-50,50] DegC

        send({'tag':'BucketRain',
              'ts':ts,
              'BucketRain_accumulation_mm':20*rhv[config.DAQ_CH_MAP['BucketRain_accumulation_mm']]})    # map 0-2.5V to 0-50mm

        if daqlv is None:
            daqlv = initdaqlv()
        rlv = daqlv.ReadAll()
        if rlv is None:
            logger.error('Unable to read LV DAQ')
            daqlv = None
            return

        ts = time.time()
        
        send({'tag':'PIR',
              'ts':ts,
              'PIR_mV':rlv[config.DAQ_CH_MAP['PIR_mV']]/1e-3,   # from Volt to mV
              'PIR_case_V':rhv[config.DAQ_CH_MAP['PIR_case_V']],
              'PIR_dome_V':rhv[config.DAQ_CH_MAP['PIR_dome_V']]})

        send({'tag':'PSP',
              'ts':ts,
              'PSP_mV':rlv[config.DAQ_CH_MAP['PSP_mV']]/1e-3})  # from Volt to mV

    except:
        logger.exception(traceback.format_exc())


def taskUltrasonicWind():
    try:
        with serial.Serial(config.USWIND_PORT[0],config.USWIND_PORT[1],timeout=0.1) as s:
            #s.write('M0!\r')       # the sensor is slow at processing commands...
            for c in 'M0!\r':
                s.write(c)
                s.flushOutput()
            line = []
            for i in range(20):     # should be ~17 chr
                c = s.read(size=1)
                if len(c):
                    line.extend(c)
                if c == '\r':
                    break
            #logger.debug(''.join(line))
            #logger.debug([ord(c) for c in line])
            line = ''.join(line).strip().split(' ')
            if len(line) <= 0:
                logger.warning('taskUltrasonicWind(): no response from Ultrasonic anemometer')
                return
                
            if '0' == line[0] and '*' == line[3][2]:    # '0' is the address of the sensor
                d = {'tag':'UltrasonicWind',
                     'ts':time.time(),
                     'UltrasonicWind_apparent_speed_mps':float(line[1]),
                     'UltrasonicWind_apparent_direction_deg':float(line[2])}
                send(d)
            else:
                logger.error('Failed to read ultrasonic anemometer. {}'.format(line))
    except:
        logger.exception(traceback.format_exc())


def taskOpticalRain():
    try:
        with serial.Serial(config.OPTICALRAIN_PORT[0],config.OPTICALRAIN_PORT[1],timeout=0.1) as s:
            s.write('A')
            line = []
            for i in range(30):
                c = s.read(size=1)
                if len(c):
                    line.append(c)
                if c == '\r':
                    break
            line = ''.join(line).rstrip()

            if len(line) <= 0:
                logger.warning('taskOpticalRain(): no response from Optical Rain Gauge')
                return

            d = {'tag':'OpticalRain',
                 'ts':time.time(),
                 'OpticalRain_weather_condition':line[0:2],
                 'OpticalRain_instantaneous_mmphr':float(line[3:7]),
                 'OpticalRain_accumulation_mm':float(line[8:15])}
            send(d)

            # - - -
            # reset accumulation at UTC midnight
            ts = datetime.utcnow()
            if not ts.day == taskOpticalRain.last_reset_day:
                logging.info('Accumulation Data Reset')
                s.write('R')
                for i in range(10):
                    r = s.read()
                    if len(r):  # whatever it is, as long as the sensor responded
                        taskOpticalRain.last_reset_day = ts.day
                        break
    except:
        logger.exception(traceback.format_exc())
taskOpticalRain.last_reset_day = datetime.utcnow().day


def taskHeartbeat():
    try:
        # global vs leaked static var of function... both evil.
        if datetime.utcnow() - send.last_transmitted > timedelta(seconds=60):
            send({})
    except:
        logger.exception(traceback.format_exc())


LoopingCall(taskWDT).start(61,now=False)
LoopingCall(taskDAQ).start(1)
LoopingCall(lambda: taskMisc(send)).start(10,now=False)
LoopingCall(taskUltrasonicWind).start(1,now=False)
LoopingCall(taskOpticalRain).start(1)
#LoopingCall(lambda: taskBME280(send)).start(60,now=False)
LoopingCall(taskHeartbeat).start(10,now=False)


logger.debug('starting reactor()...')
reactor.run()
del daqhv
del daqlv
logger.info('Terminated')
