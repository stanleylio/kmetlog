# Periodically broadcast its own IP? or services?
# service discovery at UDP 9005
#
# Wouldn't need this if DHCP works.
#
# ... there's no limit to the complexity - a host can hosts multiple services at multiple ports...
# or the full-blown N-to-N, "every host has potentially sensor feeds that other hosts can read", and
# "every host is potentially interested in every other feed" - i.e., there's no longer fixed roles
# of "publisher" and "logger"
#
# Stanley H.I Lio
# hlio@hawaii.edu
# Ocean Technology Group
# SOEST, University of Hawaii
# All Rights Reserved, 2016
import sys,time,json,subprocess,traceback,socket,logging
from datetime import datetime
from twisted.internet.protocol import DatagramProtocol


'''def taskServiceBroadcast():
    try:
        # get own IP
        # assuming there's only one interface...
        proc = subprocess.Popen(['hostname -I'],stdout=subprocess.PIPE,shell=True)
        out,err = proc.communicate()
        ips = out.strip().split(' ')
        ips = filter(lambda x: x != '192.168.7.2',ips)[0]

        d = {'hostname':socket.gethostname(),'services':[['kmet1',ips,9002]]}
        line = json.dumps(d,separators=(',',':'))

        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.bind(('',0))
        s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
        s.sendto(line,('<broadcast>',9005))

        logging.debug(line)
    except KeyboardInterrupt:
        raise
    except:
        logging.debug(traceback.format_exc())'''


publishers = {}


class Noname(DatagramProtocol):
    def startProtocol(self):
        self.transport.setBroadcastAllowed(True)
    
    def datagramReceived(self,data,(host,port)):
        #logging.debug((data,host,port))
        #self.transport.write(data,(host,port))
        try:
            d = json.loads(data)
            if 'services' in d:
                for s in d['services']:
                    if 'kmet1' == s[0]:
                        logging.debug('Found publisher: ' + str(s))
                        ts = datetime.utcnow()
                        publishers[d['hostname']] = (ts,s[1],s[2])
                #print publishers

            if 'kmet1' == d.get('service_query',None):
                logging.debug('Responding to query...')
                proc = subprocess.Popen(['hostname -I'],stdout=subprocess.PIPE,shell=True)
                out,err = proc.communicate()
                ips = out.strip().split(' ')
                ips = filter(lambda x: x != '192.168.7.2',ips)[0]

                d = {'hostname':socket.gethostname(),'services':[['kmet1',ips,9002]]}
                line = json.dumps(d,separators=(',',':'))

                self.transport.write(line,(host,port))
        except:
            logging.debug(traceback.format_exc())

    def service_query(self,topic='kmet1'):
        logging.debug('Broadcasting query...')
        line = json.dumps({'service_query':topic},separators=(',',':'))
        self.transport.write(line,('<broadcast>',9005))
            

def taskServiceQuery():
    p.service_query()


if '__main__' == __name__:
    from twisted.internet.task import LoopingCall
    from twisted.internet import reactor
    import sys

    if len(sys.argv) > 1:
        period = float(sys.argv[1])
    else:
        period = 60

    logging.basicConfig(level=logging.DEBUG)

    #lcsb = LoopingCall(taskServiceBroadcast)
    #lcsb.start(period)

    p = Noname()

    lcsq = LoopingCall(taskServiceQuery)
    lcsq.start(1,now=False)

    reactor.listenUDP(9005,p)
    reactor.run()
