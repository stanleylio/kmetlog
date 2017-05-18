# https://pika.readthedocs.io/en/0.10.0/examples/twisted_example.html
#
# Stanley H.I. Lio
# hlio@hawaii.edu
# Ocean Technology Group
# University of Hawaii
# All Rights Reserved. 2017
from __future__ import division,print_function
import sys,logging,json,time,traceback,pika,socket
from os.path import expanduser,basename
sys.path.append(expanduser('~'))
from datetime import datetime,timedelta
from pika import exceptions
from pika.adapters import twisted_connection
from twisted.internet.task import LoopingCall
from twisted.internet import defer,reactor,protocol,task
from node.drivers.watchdog import reset_auto
from node.config.config_support import import_node_config
from cred import cred


logging.basicConfig(level=logging.INFO)


exchange_name = 'uhcm'
STALE = 5   # seconds
queue_name = basename(__file__)
config = import_node_config()
credentials = pika.PlainCredentials('nuc',cred['rabbitmq'])

UDP_PORT = 5642
sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.bind(('', 0))
sock.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)

D = {}
channel = None

# what kind of sorcery is this?
# also it doesn't show any exception (it just hangs there)
@defer.inlineCallbacks
def run(connection):
    global channel
    channel = yield connection.channel()
    exchange = yield channel.exchange_declare(exchange=exchange_name,type='topic',durable=True)
    queue = yield channel.queue_declare(queue=queue_name,
                                        durable=False,
                                        exclusive=True,
                                        auto_delete=True,
                                        arguments={'x-message-ttl':10*1000})
    yield channel.queue_bind(exchange=exchange_name,
                             queue=queue_name,
                             routing_key='*.m')
    yield channel.basic_qos(prefetch_count=1)
    queue_object,consumer_tag = yield channel.basic_consume(queue=queue_name,no_ack=True)

    LoopingCall(read,queue_object).start(0.01)


# ... witchcraft!
@defer.inlineCallbacks
def read(queue_object):
    ch,method,properties,body = yield queue_object.get()
    if body:
        logging.debug(body)
        d = json.loads(body)
        if 'tag' not in d:
            return

        global D
        D[d['tag']] = d
    #yield ch.basic_ack(delivery_tag=method.delivery_tag)


def taskSample():
    global D
#    print(D)

    r = {}
    
    if 'hv' in D:
        r['PAR_V'] = D['hv']['r'][config.DAQ_CH_MAP['PAR_V']]
        r['Rotronics_T_C'] = round(D['hv']['r'][config.DAQ_CH_MAP['Rotronics_T_C']]*100 - 30,4)   # from Volt to Deg.C
        r['Rotronics_RH_percent'] = round(D['hv']['r'][config.DAQ_CH_MAP['Rotronics_RH_percent']]*100,1)  # %RH
        r['RMYRTD_T_C'] = round(D['hv']['r'][config.DAQ_CH_MAP['RMYRTD_T_C']]*100 - 50,4)     # [0,1] V maps to [-50,50] DegC
        r['BucketRain_accumulation_mm'] = round(20*D['hv']['r'][config.DAQ_CH_MAP['BucketRain_accumulation_mm']],1)   # map 0-2.5V to 0-50mm

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
        m = json.dumps(r,separators=(',',':'))
        global channel
        channel.basic_publish(exchange=exchange_name,
                              routing_key='samples',
                              body=m,
                              properties=pika.BasicProperties(delivery_mode=1,  # non-persistent
                                                              content_type='text/plain',
                                                              expiration=str(60*1000),
                                                              timestamp=time.time()))

    # - - - - -
    s = '1: {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {}\n\x00'.format(
        0,                                                      # Panel temperature (kept for compatibility)
        r.get('RMYRTD_T_C',0),                                  # RTD (Deg.C)
        r.get('Rotronics_RH_percent',0),                        # Humidity (%)
        r.get('Rotronics_T_C',0),                               # Humidity_temperature
        r.get('BucketRain_accumulation_mm',0),                  # Bucket_rain_gauge
        r.get('PSP_mV',0),                                      # PSP (mV)
        r.get('PIR_mV',0),                                      # PIR (mV)
        r.get('PIR_case_V',0),                                  # PIR Case thermistor (V)
        r.get('PIR_dome_V',0),                                  # PIR Dome thermistor (V)
        r.get('RMYRTD_Fan_rpm',0),                              # RTD fan speed
        r.get('Rotronics_Fan_rpm',0),                           # Humidity fan speed
        r.get('PAR_V',0),                                       # PAR (V)
        r.get('UltrasonicWind_apparent_speed_mps',0)*1.94384,   # Relative wind speed (ultrasonic, m/s to knot)
        r.get('UltrasonicWind_apparent_direction_deg',0),       # Relative wind direction
        r.get('OpticalRain_weather_condition','  '),            # Weather condition (optical)
        r.get('OpticalRain_instantaneous_mmphr',0),             # Precipitation (optical, mm)
        r.get('OpticalRain_accumulation_mm',0),                 # Precipitation accumulation (optical)
        )
    #logger.debug(s)
    #sock.sendto(s,('<broadcast>',UDP_PORT))    # doesn't work on the KM
    for p in ['192.168.1.255','166.122.96.152']:
        try:
            sock.sendto(s,(p,UDP_PORT))
        except socket.error:
            pass
    

def taskTrim():
    global D
    for k in list(D.keys()):
        if 'ts' in D[k] and time.time() - D[k]['ts'] > STALE:
            del D[k]


def taskWDT():
    try:
        good = reset_auto()
        if good:
            logging.info('WDT good')
        else:
            logging.warning('WDT not found')
    except:
        traceback.print_exc()


parameters = pika.ConnectionParameters('localhost',5672,'/',credentials)
cc = protocol.ClientCreator(reactor,twisted_connection.TwistedProtocolConnection,parameters)
d = cc.connectTCP('localhost',5672)
d.addCallback(lambda protocol: protocol.ready)
d.addCallback(run)

LoopingCall(taskWDT).start(59,now=False)
LoopingCall(taskSample).start(1,now=False)
LoopingCall(taskTrim).start(10,now=False)

logging.info(__file__ + ' is ready')
reactor.run()
logging.info(__file__ + ' terminated')
