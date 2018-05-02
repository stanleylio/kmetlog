# Query the DAQ and publish via 0mq
#
# Stanley H.I. Lio
# hlio@hawaii.edu
# Ocean Technology Group
# University of Hawaii
# All Rights Reserved. 2018
import sys, logging, time, json, argparse, zmq
from os.path import expanduser, exists
sys.path.append(expanduser('~'))
from twisted.internet.task import LoopingCall
from twisted.internet import reactor


def daq_init():
    
    logging.debug('Initializing DAQ')
    
    if 'hv' == args.daq:
        from node.drivers.adam4017 import ADAM4017
        daq = ADAM4017('{:02d}'.format(DAQ_ID),
                       DAQ_PORT,
                       DAQ_BAUD)
        if not daq.CheckModuleName():
            logging.critical('Cannot reach the DAQ')
            return None
        if not any([daq.SetInputRange(5) for tmp in range(3)]):   # any() is short-circuited
            logging.critical('Unable to set DAQ input range')
            return None
        return daq
    elif 'lv' == args.daq:
        from node.drivers.adam4018 import ADAM4018
        daq = ADAM4018('{:02d}'.format(DAQ_ID),
                       DAQ_PORT,
                       DAQ_BAUD)
        if not daq.CheckModuleName():
            logging.critical('Cannot reach the DAQ')
            return None
        if not any([daq.SetInputRange(50e-3) for tmp in range(3)]):
            logging.critical('Unable to set DAQ input range')
            return None
        return daq
    elif 'fc' == args.daq:
        from node.drivers.adam4080 import ADAM4080
        daq = ADAM4080('{:02d}'.format(DAQ_ID),
                       DAQ_PORT,
                       DAQ_BAUD)
        if not daq.CheckModuleName():
            logging.critical('Cannot reach the DAQ')
            return
        return daq


def task():
    global daq
    try:
        if daq is None:
            daq = daq_init()

        r = daq.ReadAll()
        if r is None:
            logging.error('Unable to read DAQ')
            daq = None
            return

        d = {'tag':args.daq,
             'ts':time.time(),
             'r':r}
        m = json.dumps(d, separators=(',', ':'))
        print(m)
        socket.send_string(m)
    except:
        logging.exception('Exception in task()')
        daq = None


if '__main__' == __name__:

    logging.basicConfig(level=logging.DEBUG)
    
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description='''Query the DAQ and send through ZeroMQ. Examples:
    python3 taskDAQ.py hv /dev/ttyUSB0 7 9011
    python3 taskDAQ.py lv /dev/ttyUSB1 5 9012
    python3 taskDAQ.py fc /dev/ttyUSB2 4 9013''')
    parser.add_argument('daq', metavar='daq', type=str, help='One of {hv, lv, fc}')
    parser.add_argument('daq_port', metavar='daq_port', type=str, help='Serial port to the DAQ')
    parser.add_argument('daq_id', metavar='daq_id', type=int, help='ID of the DAQ')
    parser.add_argument('--baud', metavar='daq_baud', type=int, default=9600, help='DAQ baud rate')
    parser.add_argument('zmq_port', metavar='zmq_port', type=int, help='ZeroMQ port')
    args = parser.parse_args()

    assert args.daq in ['hv', 'lv', 'fc']
    assert exists(args.daq_port)

    DAQ_PORT = args.daq_port
    DAQ_BAUD = args.baud
    DAQ_ID = args.daq_id
    ZMQ_PORT = args.zmq_port

    # print configuration
    logging.info('{daq_config} DAQ ID {id} at {daq_port}, {daq_baud}; zmq port: {zmq_port}'.format(
        daq_config=args.daq,
        daq_port=DAQ_PORT,
        daq_baud=DAQ_BAUD,
        id=DAQ_ID,
        zmq_port=ZMQ_PORT,
        ))

    # open the ZMQ port for publishing
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind('tcp://*:{}'.format(ZMQ_PORT))

    # initialize the DAQ
    logging.info('Attempting to reach DAQ with ID{:02d} on {} at {}...'.format(DAQ_ID, DAQ_PORT, DAQ_BAUD))
    daq = daq_init()
    LoopingCall(task).start(1)

    logging.info(__file__ + ' is ready')
    reactor.run()
    del daq
    logging.info(__file__ + ' terminated')
