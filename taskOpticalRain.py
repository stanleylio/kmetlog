# Query the optical rain gauge and publish via 0mq
#
# Stanley H.I. Lio
# hlio@hawaii.edu
# Ocean Technology Group
# University of Hawaii
# All Rights Reserved. 2018
import sys, logging, time, json, zmq, argparse
from os.path import expanduser, exists
sys.path.append(expanduser('~'))
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from node.drivers.org815dr import ORG815DR


if '__main__' == __name__:

    logging.basicConfig(level=logging.DEBUG)
    
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description='''Read optical rain gauge and publish readings. Example:
    python3 taskOpticalRain.py /dev/ttyUSB7''')
    parser.add_argument('port', metavar='port', type=str, help='Serial port to the optical rain gauge')
    parser.add_argument('--baud', metavar='baud', type=int, default=1200, help='Baud rate')
    parser.add_argument('--zmq_port', metavar='zmq_port', type=int, default=9014, help='ZeroMQ port')
    args = parser.parse_args()

    OPTICALRAIN_PORT = args.port
    OPTICALRAIN_BAUD = args.baud
    ZMQ_PORT = args.zmq_port

    assert exists(args.port)

    # print configuration
    logging.info('Configuration: optical rain gauge {port}, {baud}; zmq port: {zmq_port}'.format(
        port=OPTICALRAIN_PORT,
        baud=OPTICALRAIN_BAUD,
        zmq_port=ZMQ_PORT,
        ))

    # open the ZMQ port for publishing
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind('tcp://*:{}'.format(ZMQ_PORT))

    def task():
        try:
            org = ORG815DR(OPTICALRAIN_PORT, OPTICALRAIN_BAUD)
            r = org.read()
            org.reset_accumulation_if_required()
            if r is None:
                return
            
            r['ts'] = time.time()
            r['tag'] = 'OpticalRain'
            m = json.dumps(r, separators=(',', ':'))
            print(m)
            socket.send_string(m)
        except:
            logging.exception('Exception in task()')

    LoopingCall(task).start(1)

    logging.info(__file__ + ' is ready')
    reactor.run()
    logging.info(__file__ + ' terminated')
