# Customized hack just for the old siscon software
# Relay local met data to siscon (to emulate/replace the campbell logger)
# Task: Listen for zmq broadcast, store latest readings as they come
# in, periodically format and broadcast readings via UDP.
# The output is a space-delimited string that the old siscon program expects.
# To be run on kmet-bbb up on the met. mast.
#
# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved. 2016
import zmq,sys,json,logging,traceback,math,time,socket
import logging.handlers
from twisted.internet.task import LoopingCall
from twisted.internet import reactor



UDP_PORT = 5642
PERIOD = 1     # seconds



# Logging
'''DEBUG,INFO,WARNING,ERROR,CRITICAL'''
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # "global"?
#fh = logging.handlers.RotatingFileHandler('/var/kmetlog/log/zmq2udp.log',maxBytes=1e7,backupCount=5)
#fh.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logging.Formatter.converter = time.gmtime
formatter = logging.Formatter('%(asctime)s,%(name)s,%(levelname)s,%(message)s')
#fh.setFormatter(formatter)
ch.setFormatter(formatter)
#logger.addHandler(fh)
logger.addHandler(ch)


topic = u'kmet1'
context = zmq.Context()
zsocket = context.socket(zmq.SUB)
zsocket.connect('tcp://127.0.0.1:9002')
zsocket.setsockopt_string(zmq.SUBSCRIBE,topic)
poller = zmq.Poller()
poller.register(zsocket,zmq.POLLIN)

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.bind(('', 0))
sock.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)


def send(s):
    try:
        #logger.debug(s)
        #sock.sendto(s,('<broadcast>',UDP_PORT))
        # the siscon code doesn't handle UDP broadcast messages correctly, so UDP <broadcast>
        # cannot be used.
        sock.sendto(s,('192.168.1.255',UDP_PORT))
    except:
        logger.error(traceback.format_exc())


D = {}  # latest samples of all received variables


def taskSampler():
    try:
        socks = dict(poller.poll(100))
        if zsocket in socks and zmq.POLLIN == socks[zsocket]:
            #m = zsocket.recv()
            m = zsocket.recv_string()
            #logger.debug(m)
            m = m.split(',',1)

            d = json.loads(m[1])
            # clocks on kmet-bbb and chartroom computer are not in sync, so d['ts'] and
            # time.time() on chartroom computer might be further apart than they actually
            # are.
            # this saves the chartroom computer time into the data
            assert '_ReceptionTime' not in d
            d['_ReceptionTime'] = time.time()
            D[d['tag']] = d
    except TypeError:
        logger.warning(traceback.format_exc())
        logger.warning(msg)
    except:
        logger.warning(traceback.format_exc())

def taskBroadcast():
    global D
    #print '- - - - -'
    #print sorted(D.keys())

    # emulating the Campbell Logger
    # format deduced from the siscon source code
    # total of 17 fields
    # ... yes it is space-delimited... and yes, one of the data field could also be spaces...
    # and don't ask me why a \0 is needed at the end. "because siscon wants it that way."
    # "What's the 1: for at the beginning?" "because siscon wants it that way." even though it is trivial to change it.
    # "What's that \x00 at the end" BECAUSE SISCON WANTS IT THAT WAY. NO MORE QUESTIONS.
    s = '1: {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {}\n\x00'.format(
        0,                                                      # Panel temperature (obsolete; kept for compatibility)
        D.get('RMYRTD',{}).get('RMYRTD_T_C',0),                 # RTD (Deg.C)
        D.get('Rotronics',{}).get('Rotronics_RH_percent',0),    # Humidity (%)
        D.get('Rotronics',{}).get('Rotronics_T_C',0),           # Humidity_temperature
        D.get('BucketRain',{}).get('BucketRain_accumulation_mm',0), # Bucket_rain_gauge
        D.get('PSP',{}).get('PSP_mV',0),                        # PSP (mV)
        D.get('PIR',{}).get('PIR_mV',0),                        # PIR (mV)
        D.get('PIR',{}).get('PIR_case_V',0),                    # PIR Case thermistor (V)
        D.get('PIR',{}).get('PIR_dome_V',0),                    # PIR Dome thermistor (V)
        D.get('Misc',{}).get('RMYRTD_Fan_rpm',0),               # RTD fan speed
        D.get('Misc',{}).get('Rotronics_Fan_rpm',0),            # Humidity fan speed
        D.get('PAR',{}).get('PAR_V',0),                         # PAR (V)
        D.get('UltrasonicWind',{}).get('UltrasonicWind_apparent_speed_mps',0)*1.94384,  # Relative wind speed (ultrasonic, m/s to knot)
        D.get('UltrasonicWind',{}).get('UltrasonicWind_apparent_direction_deg',0),      # Relative wind direction
        D.get('OpticalRain',{}).get('OpticalRain_weather_condition','  '),  # Weather condition (optical)
        D.get('OpticalRain',{}).get('OpticalRain_instantaneous_mmphr',0),   # Precipitation (optical, mm)
        D.get('OpticalRain',{}).get('OpticalRain_accumulation_mm',0),       # Precipitation accumulation (optical)
        )
    send(s)
    print s.strip()
    for k in D.keys():
        if time.time() - D[k]['_ReceptionTime'] > 5*PERIOD:
            del D[k]
    #D = {}

LoopingCall(taskSampler).start(0.1)
LoopingCall(taskBroadcast).start(PERIOD,now=False)

reactor.run()

zsocket.close()
