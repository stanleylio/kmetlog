# https://pika.readthedocs.io/en/0.10.0/examples/twisted_example.html
#
# Stanley H.I. Lio
# hlio@hawaii.edu
# Ocean Technology Group
# University of Hawaii
# All Rights Reserved. 2018
import sys, logging, json, time, traceback, socket, zmq
from os.path import expanduser, basename
sys.path.append(expanduser('~'))
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from twisted.python import log
from datetime import datetime,timedelta
from node.drivers.watchdog import reset_auto
from node.config.config_support import import_node_config
#from node.zmqloop import zmqloop


logging.basicConfig(level=logging.INFO)
log.startLogging(sys.stdout)


STALE_TIMEOUT = 5   # seconds
UDP_PORT = 5642

config = import_node_config()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 0))
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

context = zmq.Context()
zsocket = context.socket(zmq.SUB)
for feed in getattr(config,'subscribeto', []):
    feed = 'tcp://' + feed
    logging.info('subscribing to ' + feed)
    zsocket.connect(feed)
zsocket.setsockopt_string(zmq.SUBSCRIBE, u'')
poller = zmq.Poller()
poller.register(zsocket, zmq.POLLIN)


D = {}

def taskZMQ():
    try:
        socks = dict(poller.poll(1000))
        if zsocket in socks and zmq.POLLIN == socks[zsocket]:
            m = zsocket.recv().decode()
            logging.debug(m)
            d = json.loads(m)
            if 'tag' not in d:
                return

            global D
            D[d['tag']] = d
    except (KeyboardInterrupt, zmq.error.ZMQError):
        reactor.stop()
    except:
        logging.exception(m)


def taskSample():
    global D
#    print(D)

    r = {}
    
    if 'hv' in D:
        r['PAR_V'] = D['hv']['r'][config.DAQ_CH_MAP['PAR_V']]
        r['Rotronics_T_C'] = round(D['hv']['r'][config.DAQ_CH_MAP['Rotronics_T_C']]*100 - 30, 4)   # from Volt to Deg.C
        r['Rotronics_RH_percent'] = round(D['hv']['r'][config.DAQ_CH_MAP['Rotronics_RH_percent']]*100,1)  # %RH
        r['RMYRTD_T_C'] = round(D['hv']['r'][config.DAQ_CH_MAP['RMYRTD_T_C']]*100 - 50, 4)     # [0,1] V maps to [-50,50] DegC
        r['BucketRain_accumulation_mm'] = round(20*D['hv']['r'][config.DAQ_CH_MAP['BucketRain_accumulation_mm']], 1)   # map 0-2.5V to 0-50mm

    if 'lv' in D:
        r['PSP_mV'] = D['lv']['r'][config.DAQ_CH_MAP['PSP_mV']]/1e-3     # Volt to mV

    if 'hv' in D and 'lv' in D:
        r['PIR_mV'] = D['lv']['r'][config.DAQ_CH_MAP['PIR_mV']]/1e-3     # Volt to mV
        r['PIR_case_V'] = D['lv']['r'][config.DAQ_CH_MAP['PIR_case_V']]
        r['PIR_dome_V'] = D['lv']['r'][config.DAQ_CH_MAP['PIR_dome_V']]

    if 'UltrasonicWind' in D:
        r['UltrasonicWind_apparent_speed_mps'] = D['UltrasonicWind']['UltrasonicWind_apparent_speed_mps']
        r['UltrasonicWind_apparent_direction_deg'] = D['UltrasonicWind']['UltrasonicWind_apparent_direction_deg']

    if 'OpticalRain' in D:
        r['OpticalRain_weather_condition'] = D['OpticalRain']['weather_condition']
        r['OpticalRain_instantaneous_mmphr'] = D['OpticalRain']['instantaneous_mmphr']
        r['OpticalRain_accumulation_mm'] = D['OpticalRain']['accumulation_mm']

    if 'fc' in D:
        r['Rotronics_Fan_rpm'] = D['fc']['r'][config.DAQ_CH_MAP['Rotronics_Fan_rpm']]/2*60
        r['RMYRTD_Fan_rpm'] = D['fc']['r'][config.DAQ_CH_MAP['RMYRTD_Fan_rpm']]/2*60

    if len(r):
        r['ts'] = time.time()

        print(r)

    # - - - - -
    s = '1: {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {}\n\x00'.format(
        0,                                                      # Panel temperature (kept for compatibility)
        r.get('RMYRTD_T_C', 0),                                 # RTD (Deg.C)
        r.get('Rotronics_RH_percent', 0),                       # Humidity (%)
        r.get('Rotronics_T_C', 0),                              # Humidity_temperature
        r.get('BucketRain_accumulation_mm', 0),                 # Bucket_rain_gauge
        r.get('PSP_mV', 0),                                     # PSP (mV)
        r.get('PIR_mV', 0),                                     # PIR (mV)
        r.get('PIR_case_V', 0),                                 # PIR Case thermistor (V)
        r.get('PIR_dome_V', 0),                                 # PIR Dome thermistor (V)
        r.get('RMYRTD_Fan_rpm', 0),                             # RTD fan speed
        r.get('Rotronics_Fan_rpm', 0),                          # Humidity fan speed
        r.get('PAR_V', 0),                                      # PAR (V)
        r.get('UltrasonicWind_apparent_speed_mps', 0)*1.94384,  # Relative wind speed (ultrasonic, m/s to knot)
        r.get('UltrasonicWind_apparent_direction_deg', 0),      # Relative wind direction
        r.get('OpticalRain_weather_condition', '  '),           # Weather condition (optical)
        r.get('OpticalRain_instantaneous_mmphr', 0),            # Precipitation (optical, mm)
        r.get('OpticalRain_accumulation_mm', 0),                # Precipitation accumulation (optical)
        )
    logging.debug(s)
    #sock.sendto(s, ('<broadcast>', UDP_PORT))    # doesn't work on the KM
    #for p in ['192.168.1.255', '192.168.2.255']:
    for p in ['192.168.1.255']:
        try:
            sock.sendto(s.encode(), (p, UDP_PORT))
        except socket.error:
            pass
        except KeyboardInterrupt:
            reactor.stop()
        except:
            logging.exception(s)

def taskTrim():
    """Trim off stale entries in the cache"""
    global D
    for k in list(D.keys()):
        if 'ts' in D[k] and time.time() - D[k]['ts'] > STALE_TIMEOUT:
            del D[k]

def taskWDT():
    try:
        good = reset_auto()
        if good:
            logging.info('WDT good')
        else:
            logging.warning('WDT not found')
    except KeyboardInterrupt:
        reactor.stop()
    except:
        logging.exception('WDT error')


LoopingCall(taskZMQ).start(0.1, now=True)
LoopingCall(taskWDT).start(59, now=True)
LoopingCall(taskSample).start(1, now=False)
LoopingCall(taskTrim).start(STALE_TIMEOUT, now=False)

logging.info(__file__ + ' is ready')
reactor.run()
logging.info(__file__ + ' terminated')
