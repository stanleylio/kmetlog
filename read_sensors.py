# Generate and publish random data for debugging
# 
# Ocean Technology Group
# SOEST, University of Hawaii
# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved, 2016
import sys,zmq,logging,json
sys.path.append(r'../node')
from helper import *
from random import random
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from datetime import datetime
from adam4018 import ADAM4018


logging.basicConfig(level=logging.DEBUG)


daq = ADAM4018('01','/dev/ttyUSB0',9600)
assert daq.CheckModuleName()
assert daq.SetInputRange(50e-3)


context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind('tcp://*:9002')



def send(d):
    topic = d['tag']
    s = json.dumps(d,separators=(',',':'))
    s = 'kmet1_{topic},{msg}'.format(msg=s,topic=topic)
    logging.debug(s)
    socket.send_string(s)


def taskLight():
    r = daq.ReadAll()
    
    par = {'tag':'PAR',
         'ts':dt2ts(datetime.utcnow()),
         'par_V':r[0]*2}
    psp = {'tag':'PSP',
         'ts':dt2ts(datetime.utcnow()),
         'psp_mV':r[1]/1e-3}
    pir = {'tag':'PIR',
         'ts':dt2ts(datetime.utcnow()),
         'ir_mV':r[2]/1e-3,
         't_case_ohm':-r[6],    # need to do the math to get R from V
         't_dome_ohm':-r[7]}
    send(par)
    send(psp)
    send(pir)

'''def taskPIR():
    d = {'tag':'PIR',
         'ts':dt2ts(datetime.utcnow()),
         'ir_mV':50*random(),
         't_case_ohm':10e3*random(),
         't_dome_ohm':10e3*random()}
    send(d)

def taskPAR():
    d = {'tag':'PAR',
         'ts':dt2ts(datetime.utcnow()),
         'par_V':5*random()}
    send(d)

def taskPSP():
    d = {'tag':'PSP',
         'ts':dt2ts(datetime.utcnow()),
         'psp_mV':1e3*random()}
    send(d)

def taskPortWind():
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

def taskBME280Sample():
    d = {'tag':'BME280',
         'ts':dt2ts(datetime.utcnow()),
         'T':100*random()-40,
         'P':20*random()-10 + 101.325,
         'RH':100*random()}
    send(d)


LC = [LoopingCall(taskPIR),
      LoopingCall(taskPAR),
      LoopingCall(taskPSP),
      LoopingCall(taskPortWind),
      LoopingCall(taskStarboardWind),
      LoopingCall(taskUltrasonicWind),
      LoopingCall(taskOpticalRain),
      LoopingCall(taskBME280Sample)
      ]
for lc in LC:
    lc.start(1,now=False)'''

lc = LoopingCall(taskLight)
lc.start(1,now=False)


reactor.run()
del daq
logging.info('terminated')

