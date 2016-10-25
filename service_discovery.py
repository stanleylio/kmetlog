# Service discovery stuff
#
# To find other publishers, broadcast UDP at 9005 the json string (using topic='kmet1' as example)
#   {"service_query":"kmet1"}
# Publishers that got this message would respond the json string (kmet-bbb as example)
#   {"hostname":"kmet-bbb","services":[["kmet1","192.168.1.109",9002]]}
# To see the list of services known to this host, send
#   {"get_service_listing":"kmet1"}
#
# Wouldn't need this if DHCP/UPnP works.
#
# There's no limit to complexity - a publisher can publish multiple topics at multiple ports, and
# a subscriber can be subscribed to multiple topics from multiple publishers.
# Basically full-blown N-to-N, "every host has potentially sensor feeds that other hosts can read", and
# "every host is potentially interested in every other feed" - i.e., there's no longer fixed roles
# of "publisher" and "data logger".
#
# There's still the decision to be made: after discovery, which of those am I actually interested in?
#
# In principle, to see what services are out there you can just send a query broadcast and wait for response.
# So no daemon and dictionary of services and fresh/stale detection needed.
# But the services would still need to host a daemon to listen for query broadcast.
#
#
# Stanley H.I. Lio
# hlio@hawaii.edu
# Ocean Technology Group
# SOEST, University of Hawaii
# All Rights Reserved, 2016
import sys,json,subprocess,traceback,socket,logging,time
from twisted.internet.protocol import DatagramProtocol


topic = 'kmet1'
best_before = 5*60  # second. a service listing is considered stale if it was last updated over this many seconds ago
min_period = 5      # query broadcast interval when there's no known service
max_period = 60     # query broadcast interval when there is at least one known service

assert max_period < best_before


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

            if d.get('service_query',None) == topic:
                logging.debug('Responding to query from ' + host)
                ip = getIP()

                d = {'hostname':self._hostname,'service_response':[[topic,ip,9002]]}
                # in an alternate universe...
                #d = {'hostname':self._hostname,'service_response':[topic1,topic2,topic3...]}
                line = json.dumps(d,separators=(',',':'))

                self.transport.write(line,(host,port))

            if d.get('get_service_listing',None) == topic:
                tmp = self.get_publisher_list()
                self.transport.write(json.dumps(tmp,separators=(',',':')),(host,port))
        except:
            logging.debug(traceback.format_exc())
            logging.debug(data)

    def service_query(self,topic='kmet1'):
        """Query everyone for the given topic via UDP broadcast.
Whoever publishing this topic would respond with its own IP."""
        logging.debug('Broadcasting query...')
        line = json.dumps({'service_query':topic},separators=(',',':'))
        self.transport.write(line,('<broadcast>',9005))

    def get_publisher_list(self):
        # remove stale entries
        # tricky. this won't work if the time limit is bigger than the query broadcast interval.
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


if '__main__' == __name__:
    from twisted.internet import reactor
    import sys

    logging.basicConfig(level=logging.DEBUG)
    #logging.basicConfig(level=logging.INFO)

    if len(sys.argv) == 1:
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        sock.settimeout(5)
        sock.sendto('{"get_service_listing":"kmet1"}',('127.0.0.1',9005))
        print('waiting for response...')
        try:
            d,h = sock.recvfrom(1024)
        except socket.timeout:
            print('Daemon not running. try "python service_discovery.py 1"')
        print d
        print h
        sys.exit()

    # - - -

    period = float(sys.argv[1])

    p = ServiceDiscovery()
    reactor.listenUDP(9005,p)

    def haha():
        p.service_query()
        if len(p.get_publisher_list()) <= 0:
            reactor.callLater(min_period,haha)
        else:
            reactor.callLater(max_period,haha)
    haha()
    reactor.run()
