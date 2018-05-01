# Query the ultrasonic anemometer and publish via 0mq
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
from node.drivers.rmy85106 import RMY85106


if '__main__' == __name__:

    logging.basicConfig(level=logging.DEBUG)
    
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description='''Read ultrasonic anemometer and publish readings. Example:
    python3 taskWind.py /dev/ttyUSB6 9015''')
    parser.add_argument('port', metavar='port', type=str, help='Serial port to the ultrasonic anemometer')
    parser.add_argument('--baud', metavar='baud', type=int, default=9600, help='Baud rate')
    parser.add_argument('--zmq_port', metavar='zmq_port', type=int, default=9015, help='ZeroMQ port')
    args = parser.parse_args()

    USWIND_PORT = args.port
    USWIND_BAUD = args.baud
    ZMQ_PORT = args.zmq_port

    assert exists(args.port)

    # print configuration
    logging.info('Configuration: anemometer {port}, {baud}; zmq port: {zmq_port}'.format(
        port=USWIND_PORT,
        baud=USWIND_BAUD,
        zmq_port=ZMQ_PORT,
        ))

    # open the ZMQ port for publishing
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind('tcp://*:{}'.format(ZMQ_PORT))

    def task():
        try:
            rmy = RMY85106(USWIND_PORT, USWIND_BAUD)
            r = rmy.read()
            if r is None:
                return
            
            d = {'tag':'UltrasonicWind',
                 'ts':time.time(),
                 'UltrasonicWind_apparent_speed_mps':r['v'],
                 'UltrasonicWind_apparent_direction_deg':r['d']}
            m = json.dumps(d, separators=(',', ':'))
            print(m)
            socket.send_string(m)
        except:
            logging.exception('Exception in task()')

    LoopingCall(task).start(1)

    logging.info(__file__ + ' is ready')
    reactor.run()
    logging.info(__file__ + ' terminated')
