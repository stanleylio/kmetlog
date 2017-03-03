# Service discovery stuff
#
# To run this as a daemon:
#   python service_discovery.py
# To initiate a service search:
#   python service_discovery.py q
#
# Three jobs:
#   It responds to requests from other hosts looking for the 'kmet1' service;
#   It listens for service announcements from other hosts and maintains a list of hosts wiath that service;
#   It serves that list of hosts offering the 'kmet1' service for processes on this machine (though there's
#       nothing stopping the other hosts from querying for that list).
#
# ... wouldn't need this if DNS works...
#
# Run this script directly and it would handle the query-respond as a daemon;
# Run this script with the argument 'q' and it would return the list of known hosts offering
# the 'kmet1' service.
#
# The Protocol (on UDP PORT):
# To find other hosts, broadcast the string (using topic='kmet1' as example)
#   {"service_query":"kmet1"}
# Publishers that got this message would respond with the string (using kmet-bbb as example)
#   {"hostname":"kmet-bbb","services":[["kmet1","192.168.1.109",9002]]}
# To see the list of hosts with the kmet1 service, send
#   {"get_service_listing":"kmet1"}
#
# - - - - -
# A publisher can publish multiple topics at multiple ports, and a subscriber can subscribe
# to multiple topics from multiple publishers.
# Basically N-to-N: "every host has sensor feeds that other hosts may read", and "every host
# is potentially interested in other feeds" - i.e. there's no longer fixed roles of
# "publisher" and "data logger".
#
# Yet there's still the decision to be made: after discovery, which of those am I actually
# interested in?
#
# In principle, this host does not need to maintain an up-to-date list of known hosts at all
# time - you can initiate a query broadcast when such list is needed. Small delay, small
# price to pay.
#
# The host would still need a daemon to respond to query broadcasts from other hosts.
#
#
# Stanley H.I. Lio
# hlio@hawaii.edu
# Ocean Technology Group
# SOEST, University of Hawaii
# All Rights Reserved, 2016
import sys,json,subprocess,traceback,socket,logging,time
from twisted.internet.protocol import DatagramProtocol


PORT = 9005


topic = 'kmet1'
best_before = 5*60      # second. a service listing is considered stale if it was last updated over this many seconds ago
max_response_time = 2   # # of seconds to wait for service providers to respond


def getIP():
    proc = subprocess.Popen(['hostname -I'],stdout=subprocess.PIPE,shell=True)
    out,err = proc.communicate()
    ips = out.strip().split(' ')
    ips = filter(lambda x: x != '192.168.7.2',ips)[0]
    return ips


class ServiceDiscovery(DatagramProtocol):
    _hostname = socket.gethostname()
    _publishers = {}     # all currently known publishers
    
    def startProtocol(self):
        self.transport.setBroadcastAllowed(True)
    
    def datagramReceived(self,data,(host,port)):
        """Process incoming messages. Expecting two types of messages:
1. it's a "service_query": respond if it's looking for the topic 'kmet1';
2. it's a "service_response": add this publisher if it has the topic 'kmet1'"""
        #logging.debug((data,host,port))
        #self.transport.write(data,(host,port))
        try:
            d = json.loads(data)

            #if d['hostname'] == self._hostname:   # exclude self
                #logging.debug('ignore msg from oneself: ' + data)
                #return

            if 'service_response' in d:
                if 'hostname' not in d:
                    logging.debug('missing "hostname": ' + data)
                    return

                # basically it's not up to the driver to decide whether to list oneself as a publisher
                for s in d['service_response']:
                    if topic != s[0]:
                        logging.debug("not what I'm interested in: " + data)
                        return
                    
                    # No spoofing? Now only the publisher itself can announce its own presence.
                    # That means you can't have dedicated "service listing provider" (which
                    # doesn't itself publish).
                    #
                    # If only publisher itself can announce its own presence, then the response
                    # doesn't have to include ip or port since you know where it comes from, and
                    # the port is fixed across the entire project.
                    if s[1] != host:
                        logging.debug("announcement not coming from the publisher itself: " + data)
                        return

                    #logging.info('Found publisher: ' + str(s))
                    if d['hostname'] not in self._publishers:
                        logging.info('Added publisher: ' + d['hostname'] + ', ' + str(s))
                    
                    self._publishers[d['hostname']] = (time.time(),s[1],s[2])

                    #print self._publishers

            elif d.get('service_query',None) == topic:
                logging.debug('Responding to query from ' + host)
                ip = getIP()

                d = {'hostname':self._hostname,'service_response':[[topic,ip,9002]]}
                # in an alternate universe...
                #d = {'hostname':self._hostname,'service_response':[topic1,topic2,topic3...]}
                line = json.dumps(d,separators=(',',':'))

                self.transport.write(line,(host,port))

            elif d.get('get_service_listing',None) == topic:
                self.service_query()    # query service providers only on demand
                # problem is, the service_response won't get processed until this returns
                # so don't sleep, use callLater()
                #time.sleep(max_response_time)
                #tmp = self.get_publisher_list()
                #self.transport.write(json.dumps(tmp,separators=(',',':')),(host,port))
                def tmp():
                    tmp = self.get_publisher_list()
                    self.transport.write(json.dumps(tmp,separators=(',',':')),(host,port))
                reactor.callLater(max_response_time,tmp)
            else:
                #logging.debug(data)
                pass
        except:
            logging.debug(traceback.format_exc())
            logging.debug(data)

    def service_query(self,topic='kmet1'):
        """Query everyone for the given topic via UDP broadcast.
Whoever publishing this topic would respond with its own IP."""
        logging.debug('Broadcasting query...')
        line = json.dumps({'service_query':topic},separators=(',',':'))
        self.transport.write(line,('<broadcast>',PORT))

    def get_publisher_list(self):
        # remove stale entries
        for k in self._publishers.keys():
            host = self._publishers[k]
            if time.time() - host[0] > best_before:
                 del self._publishers[k]
        
        # create a list
        pl = []
        for k in self._publishers.keys():
            host = self._publishers[k]
            pl.append([k,'{}:{}'.format(host[1],host[2])])
        return pl

def get_publisher_list():
    """Ask the local daemon for a list of known hosts with the kmet1 service"""
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.settimeout(max_response_time + 1)
    sock.sendto('{"get_service_listing":"kmet1"}',('127.0.0.1',PORT))
    print('waiting for response...')
    try:
        d,h = sock.recvfrom(1024)
        logging.debug(d + ' from ' + repr(h))
        return json.loads(d)
    except socket.timeout:
        logging.error('Daemon not running. Run "python service_discovery.py" (optionally in the background) first.')
        return []
    except:
        logging.error(traceback.format_exc())
        return []


if '__main__' == __name__:
    from twisted.internet import reactor
    import sys

    #logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) == 1:
        p = ServiceDiscovery()
        reactor.listenUDP(PORT,p)
        p.service_query()
        reactor.run()
    elif sys.argv[1] == 'q':
        for r in get_publisher_list():
            print r
