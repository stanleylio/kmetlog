# Stuff for getting readings from the ultrasonic anemometer
#
# Stanley H.I. Lio
# hlio@hawaii.edu
# Ocean Technology Group
# University of Hawaii
# All Rights Reserved. 2018
import sys,logging,time,traceback,json,zmq
from os.path import expanduser
sys.path.append(expanduser('~'))
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from node.config.config_support import import_node_config
from node.drivers.rmy85106 import RMY85106


logging.basicConfig(level=logging.DEBUG)


context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind('tcp://*:9015')

config = import_node_config()


def task():
    try:
        rmy = RMY85106(config.USWIND_PORT[0],config.USWIND_PORT[1])
        r = rmy.read()
        if r is None:
            return
        
        d = {'tag':'UltrasonicWind',
             'ts':time.time(),
             'UltrasonicWind_apparent_speed_mps':r['v'],
             'UltrasonicWind_apparent_direction_deg':r['d']}
        m = json.dumps(d,separators=(',',':'))

        print(m)
        socket.send_string(m)
    except:
        traceback.print_exc()


LoopingCall(task).start(1)

logging.info(__file__ + ' is ready')
reactor.run()
logging.info(__file__ + ' terminated')
