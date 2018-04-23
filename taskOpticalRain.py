# Stuff for getting readings from the optical rain gauge
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
from node.drivers.org815dr import ORG815DR


logging.basicConfig(level=logging.DEBUG)


context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind('tcp://*:9014')

config = import_node_config()


def task():
    try:
        org = ORG815DR(config.OPTICALRAIN_PORT[0],config.OPTICALRAIN_PORT[1])
        r = org.read()
        org.reset_accumulation_if_required()
        if r is None:
            return
        r['ts'] = time.time()
        r['tag'] = 'OpticalRain'
        m = json.dumps(r,separators=(',',':'))
        print(m)
        socket.send_string(m)
    except:
        traceback.print_exc()


LoopingCall(task).start(1)

logging.info(__file__ + ' is ready')
reactor.run()
logging.info(__file__ + ' terminated')
