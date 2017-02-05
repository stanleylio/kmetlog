# Generate and publish random data for debugging
# 
# Ocean Technology Group
# SOEST, University of Hawaii
# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved, 2016
import sys,zmq,logging
sys.path.append(r'..')
from node.helper import *
from random import random,choice
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from datetime import datetime
import json


logging.basicConfig(level=logging.DEBUG)


context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind('tcp://*:9002')


def send(d):
    topic = d['tag']
    s = json.dumps(d,separators=(',',':'))
    s = 'kmet1_{topic},{msg}'.format(msg=s,topic=topic)
    logging.debug(s)
    socket.send_string(s)


def taskPIR():
    d = {'tag':'PIR',
         'ts':dt2ts(datetime.utcnow()),
         'ir_mV':round(50*random(),3),
         't_case_V':round(2.5*random(),3),
         't_dome_V':round(2.5*random(),3)}
    send(d)

def taskPAR():
    d = {'tag':'PAR',
         'ts':dt2ts(datetime.utcnow()),
         'par_V':round(5*random(),3)}
    send(d)

def taskPSP():
    d = {'tag':'PSP',
         'ts':dt2ts(datetime.utcnow()),
         'psp_mV':round(1e3*random(),2)}
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
         'apparent_speed_mps':round(50*random(),1),
         'apparent_direction_deg':round(360*random(),1)}
    send(d)

def taskOpticalRain():
    conds = ['  ','R-','R ','R+','S-','S ','S+','P-','P ','P+']
    d = {'tag':'OpticalRain',
         'ts':dt2ts(datetime.utcnow()),
         'weather_condition':choice(conds),
         'instantaneous_mmphr':round(100*random(),1),
         'accumulation_mm':round(1000*random(),1)}
    send(d)

def taskRotronics():
    d = {'tag':'Rotronics',
          'ts':dt2ts(),
          'T':round(100*random()-30.0,2),    # convert from Volt to Deg.C
          'RH':round(100*random(),1)}        # %RH
    send(d)

def taskRMYRTD():
    d = {'tag':'RMYRTD',
         'ts':dt2ts(),
         'T':round(100*random()-50,3)}       # [0,1] V maps to [-50,50] DegC
    send(d)

def taskBucketRain():
    d = {'tag':'BucketRain',
         'ts':dt2ts(),
         'accumulation_mm':round(50*random(),1)}    # map 0-2.5V to 0-50mm
    send(d)

def taskMisc():
    d = {'tag':'Misc',
         'ts':dt2ts(),
         'RadFan1_rpm':round(6000*random(),1),     # rotronics humidity shield
         'RadFan2_rpm':round(6000*random(),1),     # RMY RTD shield
         }
    send(d)

def taskBME280Sample():
    d = {'tag':'BME280',
         'ts':dt2ts(datetime.utcnow()),
         'T':round(100*random()-40,2),
         'P':round(20*random()-10 + 101.325,3),
         'RH':round(100*random(),2)}
    send(d)


LC = [LoopingCall(taskPIR),
      LoopingCall(taskPAR),
      LoopingCall(taskPSP),
      #LoopingCall(taskPortWind),
      #LoopingCall(taskStarboardWind),
      LoopingCall(taskUltrasonicWind),
      LoopingCall(taskOpticalRain),
      LoopingCall(taskBME280Sample),
      LoopingCall(taskRotronics),
      LoopingCall(taskRMYRTD),
      LoopingCall(taskBucketRain),
      LoopingCall(taskMisc),]
for lc in LC:
    lc.start(50*random()/10. + 1,now=False)
    #lc.start(1,now=False)

reactor.run()
print('done')

